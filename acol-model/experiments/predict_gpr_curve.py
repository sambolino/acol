"""Return a complete GPR curve and selected prediction as JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


def gpr_predict(model, features):
    """Return mean and deviation in the model's log10 target space."""
    transformed = model.named_steps["preprocess"].transform(features)
    return model.named_steps["gpr"].predict(transformed, return_std=True)


def log10_interval_to_linear(mean, deviation):
    """Convert a log10 prediction and deviation to a 95% linear interval."""
    mean = np.asarray(mean)
    deviation = np.asarray(deviation)
    return 10**mean, 10 ** (mean - 1.96 * deviation), 10 ** (mean + 1.96 * deviation)


def _prepare_transition(process: str, values: dict[str, str]) -> tuple[pd.DataFrame, dict[str, object]]:
    data = pd.read_csv(Path("data/runtime") / f"{process}.csv").copy()

    if process == "EEX":
        data["element"] = data["reactants"].str.extract(r"^([A-Za-z]+)")[0]
        initial_n = int(values["initial_n"])
        delta_n = int(values["delta_n"])
        transition = data.loc[
            (data["element"] == values["element"])
            & (data["reactant_n_max"] == initial_n)
            & (data["delta_n_max"] == delta_n)
        ]
        features = {"initial_n": initial_n, "delta_n": delta_n, "element": values["element"]}
    elif process in ("HAS", "HPN"):
        data["element"] = data["reactants"].str.extract(r"^([A-Za-z]+)")[0]
        lower_n = int(values["lower_initial_n"])
        upper_n = int(values["upper_initial_n"])
        transition = data.loc[
            (data["element"] == values["element"])
            & (data["reactant_n_min"] == lower_n)
            & (data["reactant_n_max"] == upper_n)
        ]
        features = {
            "lower_initial_n": lower_n,
            "upper_initial_n": upper_n,
            "element": values["element"],
        }
    elif process == "EDR":
        data["species"] = data["reactants"].str.extract(r"^([A-Za-z]+)")[0]
        data["vibrational_level"] = data["reactants"].str.extract(r"v'=(\d+)")[0].fillna(0).astype(int)
        lower_n = int(values["lower_final_n"])
        upper_n = int(values["upper_final_n"])
        vibrational_level = int(values["vibrational_level"])
        transition = data.loc[
            (data["species"] == values["species"])
            & (data["product_n_min"].fillna(0) == lower_n)
            & (data["product_n_max"].fillna(0) == upper_n)
            & (data["vibrational_level"] == vibrational_level)
        ]
        features = {
            "lower_final_n": lower_n,
            "upper_final_n": upper_n,
            "vibrational_level": vibrational_level,
            "species": values["species"],
        }
    elif process == "ERO":
        data["element"] = data["reactants"].str.extract(r"^([A-Za-z]+)")[0]
        state_values = {
            "ion_n": int(values["ion_n"]),
            "initial_neutral_n": int(values["initial_neutral_n"]),
            "final_neutral_n": int(values["final_neutral_n"]),
            "final_excited_n": int(values["final_excited_n"]),
        }
        transition = data.loc[
            (data["element"] == values["element"])
            & (data["reactant_n_min"] == state_values["ion_n"])
            & (data["reactant_n_max"] == state_values["initial_neutral_n"])
            & (data["product_n_min"] == state_values["final_neutral_n"])
            & (data["product_n_max"] == state_values["final_excited_n"])
        ]
        features = dict(state_values, element=values["element"])
    else:
        raise ValueError(f"Unsupported GPR process: {process}")

    if transition.empty:
        raise ValueError("No matching tabulated transition was found")

    return transition.sort_values("x"), features


def predict_curve(process: str, values: dict[str, str]) -> dict[str, object]:
    temperature = float(values["temperature"])
    transition, feature_values = _prepare_transition(process, values)
    observed_min = float(transition["x"].min())
    observed_max = float(transition["x"].max())
    observed_span = observed_max - observed_min
    padding = observed_span * 0.05 if observed_span else max(observed_min * 0.05, 1.0)
    curve_min = max(1.0, min(observed_min - padding, temperature - padding))
    curve_max = max(observed_max + padding, temperature + padding)
    temperatures = np.unique(np.append(np.linspace(curve_min, curve_max, 319), temperature))

    features = pd.DataFrame({
        "log10_temperature": np.log10(temperatures),
        **{name: value for name, value in feature_values.items()},
    })
    selected_features = pd.DataFrame({
        "log10_temperature": [np.log10(temperature)],
        **{name: [value] for name, value in feature_values.items()},
    })
    model = joblib.load(Path("artifacts") / f"gpr_{process.lower()}_global" / "model.joblib")
    predicted_log_y, std_log_y = gpr_predict(model, features)
    predicted_y, lower_y, upper_y = log10_interval_to_linear(predicted_log_y, std_log_y)
    selected_log_y, selected_std_y = gpr_predict(model, selected_features)
    selected_y, selected_lower_y, selected_upper_y = log10_interval_to_linear(
        selected_log_y, selected_std_y
    )
    selected_index = int(np.flatnonzero(temperatures == temperature)[0])
    predicted_y[selected_index] = selected_y[0]
    lower_y[selected_index] = selected_lower_y[0]
    upper_y[selected_index] = selected_upper_y[0]

    return {
        "process": process,
        "reaction": str(transition["reaction"].iloc[0]),
        "x_unit": str(transition["x_unit"].iloc[0]),
        "y_unit": str(transition["y_unit"].iloc[0]),
        "observed_x_min": observed_min,
        "observed_x_max": observed_max,
        "curve_x": temperatures.tolist(),
        "curve_y": predicted_y.tolist(),
        "lower_95_curve_y": lower_y.tolist(),
        "upper_95_curve_y": upper_y.tolist(),
        "observed_x": transition["x"].astype(float).tolist(),
        "observed_y": transition["y"].astype(float).tolist(),
        "temperature_k": temperature,
        "predicted_y": float(selected_y[0]),
        "lower_95_y": float(selected_lower_y[0]),
        "upper_95_y": float(selected_upper_y[0]),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("process", choices=("EEX", "HAS", "HPN", "EDR", "ERO"))
    parser.add_argument("values_json")
    arguments = parser.parse_args()
    print(json.dumps(predict_curve(arguments.process, json.loads(arguments.values_json))))
