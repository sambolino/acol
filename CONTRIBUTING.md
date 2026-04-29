# Contributing

This repository contains the ACol-specific customization layer for a VAMDC NodeSoftware node.

## Important Locations

Local node code:

```text
node/models.py
node/queryfunc.py
node/dictionaries.py
node/views.py
node/forms.py
```
## Upstream Dependency

This node is built on top of VAMDC NodeSoftware:

https://github.com/VAMDC/NodeSoftware

Relevant components:

- `vamdctap/generators.py`  
  Responsible for XSAMS XML generation (calls model `XML()` methods via `checkXML()`)

- `vamdctap/sqlparse.py`  
  Handles TAP query parsing

- `vamdctap/`  
  Core TAP and XSAMS infrastructure

In local deployments, this repository is expected to be available in the Python path.

`generators.py` is especially important: it creates XSAMS XML and calls object-level `XML()` methods through `checkXML()`.

## Core Principle

The database model should describe the scientific data.
The XSAMS hierarchy should be constructed dynamically when exporting.

Do not store XML-shaped structures in the database unless there is a real domain reason.

## XML Overrides

Some XSAMS structures cannot be produced correctly by the upstream generator alone.

In those cases, define an `XML()` method on the relevant model class.

Current examples:

```text
Atom.XML()
TabulatedData.XML()
```

These overrides are picked up by upstream `checkXML()` in the upstream
`generators.py`

Use XML overrides when:

* the upstream generator cannot express the required nesting
* multiple child elements must be emitted explicitly
* runtime-attached attributes are needed
* schema-required wrappers do not match the persistent model

Avoid XML overrides when a simple dictionary mapping is enough.

## Where to Change What

### `models.py`

Use for:

* persistent fields
* model relationships
* custom `XML()` overrides when necessary

### `dictionaries.py`

Use for:

* VAMDC returnable mappings
* restrictable mappings
* mapping generator keys to model/runtime attributes

### `queryfunc.py`

Use for:

* query-time object shaping
* attaching runtime attributes
* grouping ions
* building XSAMS-compatible transient structures
* attaching sources and tabulated data to collisions

### Upstream `generators.py`

Normally do not edit this.

Understand it, but prefer local overrides in this repository.

## Common Pattern

1. Store normalized data in the database.
2. Use `queryfunc.py` to assemble runtime structure.
3. Use `dictionaries.py` to expose values to the generator.
4. Use `XML()` overrides only when the upstream generator cannot produce valid XSAMS.

## Current Custom Behavior

* atomic XML generation supports multiple ions inside one atom
* isotope mass information is conditionally emitted
* tabulated data points directly to collisions
* source references are resolved through data-source groupings
* XSAMS `DataSet` structures are generated dynamically at query time

## Do Not Commit

```text
local_settings.py
.env
data/
static_old/
static/plots/
*.log
*.sql
*.xsams
__pycache__/
*.pyc
```

## Testing Checklist

After changes, verify:

* Django page loads
* admin loads
* TAP query works
* generated XSAMS validates
* XML display still works
* no secrets are committed

