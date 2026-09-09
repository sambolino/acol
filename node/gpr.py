"""Bridge between the Django node and the separately isolated GPR environment."""

import json
import math
import os
import subprocess

from django.conf import settings


SUPPORTED_MODELS = ('EEX', 'HAS', 'HPN', 'EDR', 'ERO')


def _positive_float(data, name, label):
    try:
        value = float(data.get(name, ''))
    except (TypeError, ValueError):
        raise ValueError('%s must be a number.' % label)

    if not math.isfinite(value) or value <= 0:
        raise ValueError('%s must be greater than zero.' % label)

    return str(value)


def _integer(data, name, label, minimum=1):
    try:
        value = int(data.get(name, ''))
    except (TypeError, ValueError):
        raise ValueError('%s must be an integer.' % label)

    if value < minimum:
        raise ValueError('%s must be at least %d.' % (label, minimum))

    return str(value)


def _choice(data, name, label, choices):
    value = (data.get(name) or '').strip()

    if value not in choices:
        raise ValueError('%s must be one of: %s.' % (label, ', '.join(choices)))

    return value


def _model_arguments(process, data):
    if process == 'EEX':
        return [
            _positive_float(data, 'temperature', 'Temperature'),
            _choice(data, 'element', 'Element', ('H', 'He')),
            _integer(data, 'initial_n', 'Initial n'),
            _integer(data, 'delta_n', 'Delta n'),
        ]

    if process in ('HAS', 'HPN'):
        elements = ('H', 'He', 'K') if process == 'HAS' else ('H', 'He')
        lower = _integer(data, 'lower_initial_n', 'Lower initial n')
        upper = _integer(data, 'upper_initial_n', 'Upper initial n')

        if int(upper) < int(lower):
            raise ValueError('Upper initial n must be at least lower initial n.')

        return [
            _positive_float(data, 'temperature', 'Temperature'),
            _choice(data, 'element', 'Element', elements),
            lower,
            upper,
        ]

    if process == 'EDR':
        return [
            _positive_float(data, 'temperature', 'Temperature'),
            _choice(data, 'species', 'Species', ('K', 'Li', 'Na', 'H', 'He', 'BeD')),
            _integer(data, 'lower_final_n', 'Lower final n', minimum=0),
            _integer(data, 'upper_final_n', 'Upper final n', minimum=0),
            '--vibrational-level',
            _integer(data, 'vibrational_level', 'Vibrational level', minimum=0),
        ]

    if process == 'ERO':
        return [
            _positive_float(data, 'temperature', 'Temperature'),
            _choice(data, 'element', 'Element', ('K', 'Li', 'Na', 'H', 'He')),
            _integer(data, 'ion_n', 'Ion n'),
            _integer(data, 'initial_neutral_n', 'Initial neutral n'),
            _integer(data, 'final_neutral_n', 'Final neutral n'),
            _integer(data, 'final_excited_n', 'Final excited n'),
        ]

    raise ValueError('Choose a supported collision process.')


def predict(process, data):
    """Validate form values and execute the matching saved GPR model."""
    process = (process or '').strip().upper()

    if process not in SUPPORTED_MODELS:
        raise ValueError('Choose a supported collision process.')

    model_root = getattr(
        settings,
        'ACOL_MODEL_DIR',
        os.path.join(settings.PROJECT_DIR, 'acol-model'),
    )
    python_executable = getattr(
        settings,
        'ACOL_GPR_PYTHON',
        os.path.join(model_root, '.venv', 'bin', 'python'),
    )
    script_path = os.path.join(model_root, 'experiments', 'predict_gpr_curve.py')

    if not os.path.isfile(python_executable):
        raise RuntimeError('The configured GPR Python environment is unavailable.')

    if not os.path.isfile(script_path):
        raise RuntimeError('The prediction program for %s is unavailable.' % process)

    _model_arguments(process, data)
    values = {key: data.get(key) for key in data}
    command = [python_executable, script_path, process, json.dumps(values)]

    try:
        completed = subprocess.run(
            command,
            cwd=model_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError('The GPR calculation took too long.')
    except OSError:
        raise RuntimeError('The GPR calculation could not be started.')

    if completed.returncode != 0:
        raise RuntimeError('The GPR model could not calculate this prediction.')

    try:
        result = json.loads(completed.stdout)
    except (TypeError, ValueError):
        raise RuntimeError('The GPR model returned an invalid result.')

    result['process'] = process
    return result
