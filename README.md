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

## Repository structure

* `node/models.py` — ACol data model
* `node/dictionaries.py` — VAMDC restrictables and returnables
* `node/queryfunc.py` — query execution and runtime XSAMS preparation
* `node/views.py` — web endpoints, statistics, browsing, and plotting
* `node/forms.py` — search and plotting forms
* `templates/` — HTML templates
* `static/` — JavaScript, CSS, images, and plot assets
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

