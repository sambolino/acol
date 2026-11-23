# ACol

ACol is a VAMDC-compatible data node for atomic and molecular collision data, hosted by the Serbian Virtual Observatory.

It is built on top of the VAMDC NodeSoftware framework and exposes its data through the VAMDC-TAP interface, with results returned in XSAMS format.

## Features

* atomic and molecular collision data
* multiple reactants and products per collision
* state-resolved species
* energy-dependent cross sections, rate coefficients, and yields
* bibliographic provenance with DOI links
* Dissociative Electron Attachment data
* database overview and statistics
* interactive data browsing and plotting
* GPR and PCHIP reaction diagrams
* principal-quantum-number diagnostic plots
* XSAMS query generation and download

ACol currently supports several collision processes, including excitation, associative ionization, dissociative recombination, electron–ion–atom recombination, Penning ionization, and Dissociative Electron Attachment.

## VAMDC

ACol is implemented as a customized node based on the VAMDC NodeSoftware framework.

VAMDC provides the common infrastructure used by the node, including:

* the VAMDC-TAP query interface
* VSS2 query handling
* XSAMS data exchange
* common node software and serialization tools
* interoperability with other VAMDC databases and services

This repository contains the ACol-specific data model, mappings, query logic, XML-generation customizations, web interface, and documentation.

## Web interface

The web interface contains four main sections:

* **Overview** — statistics on collisions, species, states, and sources
* **Explore Data** — filtering, source information, plots, and raw tabulated values
* **qn plots** — diagnostic plots against principal quantum number
* **Generate XSAMS** — VAMDC-style query interface and XSAMS download

## Reaction diagrams and curve models

The **Explore Data** view includes interactive diagrams for individual reactions. Each diagram shows the tabulated database values together with two complementary curve representations:

* **Gaussian Process Regression (GPR)** — a global probabilistic model is trained for each collision-process family. The independent variable (temperature, or energy where applicable) and the target observable are represented in base-10 logarithmic space, while the remaining inputs describe the species and quantum-state transition. The models use a Matern 5/2 kernel (`nu=2.5`), a white-noise term, and target normalization. The diagram shows the posterior mean and a 95% interval, calculated in logarithmic space as `mu +/- 1.96 sigma` and transformed back to the physical unit. Shaded regions outside the range of tabulated input values identify extrapolation, where predictions should be treated with additional caution.
* **Piecewise Cubic Hermite Interpolating Polynomial (PCHIP)** — a separate shape-preserving cubic interpolation is constructed for each reaction in `log10(x)`-`log10(y)` space. It passes through the tabulated points and is intended for smooth interpolation inside their domain. PCHIP does not provide a statistical uncertainty estimate and should not be interpreted as a learned model or used as evidence for behavior outside the tabulated interval.

Using both representations makes their roles explicit: PCHIP provides a local, data-preserving reference curve, while GPR can share information across related transitions and quantify model uncertainty. The grey points in both diagrams are values stored in ACol. Interactive tooltips report the curve value and the nearest database value; GPR tooltips also report the 95% interval.

Pre-generated GPR and PCHIP diagrams are stored as self-contained HTML artifacts under `acol-model/artifacts/<model>_<process>_global/html/` and are served by the Django application when a matching reaction is opened. Diagram artifacts are available for EEX, HAS, HPN, EDR, ERO, and ENI collision-process codes. The separate **GPR predictions** interface currently evaluates saved models for EEX, HAS, HPN, EDR, and ERO and can calculate a curve at a user-selected temperature and transition.

These curves are derived representations of the published tabulated data. The original database values and their bibliographic sources remain authoritative and should be cited in scientific use.

## Repository structure

* `node/models.py` — ACol data model
* `node/dictionaries.py` — VAMDC restrictables and returnables
* `node/queryfunc.py` — query execution and runtime XSAMS preparation
* `node/views.py` — web endpoints, statistics, browsing, and plotting
* `node/forms.py` — search and plotting forms
* `node/gpr.py` — validation and execution bridge for saved GPR models
* `templates/` — HTML templates
* `static/` — JavaScript, CSS, images, and plot assets
* `acol-model/artifacts/` — saved GPR models and pre-generated GPR/PCHIP reaction diagrams
* `acol-model/data/runtime/` — process-specific data used by the prediction interface
* `acol-model/experiments/predict_gpr_curve.py` — GPR curve and uncertainty calculation
* `settings.py` — Django settings
* `local_settings.py.example` — local configuration template

## Installation

```bash
git clone git@github.com:sambolino/acol.git
cd acol
cp local_settings.py.example local_settings.py
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Edit `local_settings.py` before running the node.

VAMDC NodeSoftware must be available in the Python environment.

The production scientific database is not included in this repository.

## Deployment

ACol is typically deployed with Django using Apache/mod_wsgi or Gunicorn/nginx.

After updating Python files, restart the application service. For an Apache deployment:

```bash
sudo systemctl restart apache2
```

Deployments using collected static files may also require:

```bash
python manage.py collectstatic
```

## Citation and provenance

Users should cite the original scientific publication associated with each retrieved dataset.

When citing the software implementation, use the relevant ACol publication and the corresponding archived software release, when available.

## License

MIT

## Acknowledgment

ACol builds upon the standards, infrastructure, and NodeSoftware developed by the Virtual Atomic and Molecular Data Centre (VAMDC) Consortium.

