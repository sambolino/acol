# AGENTS.md

This repository is the ACol VAMDC node customization layer.

## Context

The upstream dependency is VAMDC NodeSoftware:

https://github.com/VAMDC/NodeSoftware

Important upstream files:
- `vamdctap/generators.py`
- `vamdctap/sqlparse.py`

Do not modify upstream NodeSoftware unless explicitly asked.

## Main files

- `node/models.py` — Django models and local XML overrides
- `node/queryfunc.py` — query-time object shaping
- `node/dictionaries.py` — VAMDC returnable/restrictable mappings
- `node/views.py` — UI and plotting endpoints
- `node/forms.py` — forms

## Rules

- Keep the persistent model normalized.
- Do not store XSAMS-shaped wrapper structures unless there is a domain reason.
- Prefer `dictionaries.py` for simple field mappings.
- Use `XML()` overrides only when upstream generation cannot express the required XSAMS structure.
- Be careful with dynamically attached runtime attributes in `queryfunc.py`.

## Testing

When possible, run:

```bash
python3 manage.py check
python3 manage.py test
