# acol

ACol is a VAMDC-compatible data node for atomic and molecular collision data.
It is built on top of the VAMDC NodeSoftware framework and exposes a relational database through the VAMDC-TAP interface, returning results in XSAMS format.

## Overview

VAMDC nodes provide a standardized interface to heterogeneous atomic and molecular databases. This node translates TAP queries into database operations and dynamically generates XSAMS XML output.

This repository contains a customized implementation with:

* adapted data models
* extended dictionary mappings
* custom query logic
* modified XML generation behavior

## Structure

* `node/models.py`
  Database schema and domain objects.

* `node/dictionaries.py`
  Mapping between database fields and XSAMS returnables.

* `node/queryfunc.py`
  Query execution logic (TAP → ORM/SQL).

* `settings.py`, `local_settings.py`
  Django configuration.

* `static/`, `templates/`
  Minimal UI and XML visualization tools.

## Key Concepts

* **XSAMS**: XML schema used as output format in VAMDC.
* **Dictionaries**: Define how internal data maps to XSAMS fields.
* **Dynamic generation**: XML structures are constructed at query time, not stored.

## Setup

```bash
git clone git@github.com:sambolino/acol.git
cd acol
```

Configure local settings:

```bash
cp local_settings.py.example local_settings.py
```

Edit database credentials and paths.

Run:

```bash
python manage.py runserver
```

## Deployment

Typically deployed with:

* Apache + mod_wsgi
  or
* Gunicorn + nginx

## Notes

* This repository contains node-specific customizations only.
* VAMDC NodeSoftware is expected as an external dependency.
* Some static/template files are retained for compatibility with upstream behavior.

## License

MIT

