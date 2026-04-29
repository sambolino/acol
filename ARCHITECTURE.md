
---

# `ARCHITECTURE.md`

```markdown
# Architecture

## Conceptual Overview

ACol follows the standard VAMDC node architecture: a Django-based middleware layer that translates standardized queries into database operations and serializes results into XSAMS XML.

The system is not a static data provider. Instead, it dynamically constructs a hierarchical data model at query time.

## Layers

### 1. Data Layer (Database)

Relational database storing:
- species
- states
- processes (collisions)
- tabulated data

No XSAMS structure is stored explicitly.

---

### 2. Model Layer (`models.py`)

Defines ORM representation of domain entities.

Customizations include:
- explicit handling of atomic/molecular species
- support for tabulated datasets and data sources
- preparation for dynamic grouping (e.g. ions)

---

### 3. Mapping Layer (`dictionaries.py`)

Central abstraction translating:
- database fields → XSAMS returnables
- query constraints → database filters

Originally partially hardcoded, now simplified and made more explicit.

This layer defines *what* is exposed, not *how* it is computed.

---

### 4. Query Layer (`queryfunc.py`)

Core execution logic:
- parses TAP query constraints
- builds ORM/SQL queries
- attaches additional metadata
- prepares objects for XML generation

Supports custom logic beyond direct field mapping when needed.

---

### 5. Generation Layer (NodeSoftware `generators.py`)

Transforms query results into XSAMS.

Key customization principles:
- override default XML generation where needed
- dynamically construct missing structures
- inject metadata (e.g. dataset descriptions)

Example:
- atomic XML generation extended to support multiple ions via iteration
- hierarchical structures built at runtime instead of stored

---

### 6. Output Layer (XSAMS)

Final output:
- XML document conforming to XSAMS schema
- constructed from object graph at runtime

The object model (see Fig. 2 in accompanying documentation) represents the logical structure used during generation.

---

## Design Decisions

### Dynamic vs Static Representation

Instead of storing full XSAMS-compatible structures in the database:
- minimal relational schema is used
- hierarchical XML is assembled dynamically

This avoids redundancy and keeps the database normalized.

---

### Customization Strategy

Rather than modifying NodeSoftware globally:
- overrides are localized (models, dictionaries, query layer)
- generator behavior is extended where necessary

This preserves compatibility with upstream updates.

---

### Separation of Concerns

- `models.py`: structure
- `dictionaries.py`: semantics
- `queryfunc.py`: execution
- `generators.py`: serialization

---

## Known Trade-offs

- Tight coupling to NodeSoftware internals
- Legacy Django version constraints
- Partial duplication of static/templates for compatibility
- Some XSAMS elements require manual construction due to schema mismatch

---

## Future Directions

- decouple from NodeSoftware via abstraction layer
- introduce intermediate representation (IR) for query planning
- unify atomic and molecular handling
- improve schema coverage (e.g. molecular states, weights)

