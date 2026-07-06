---
title: API reference
---

# API reference

This page summarizes the public surface of the package. Imports below are
relative to the top-level `iucn_get_data` module:

```python
from iucn_get_data import (
    Typology, Realm, Biome, FunctionalGroup,
    get_realms, get_biomes, get_groups,
    EcosystemMap, VectorMap, RasterMap,
    open_ecosystem_map, list_engines,
)
```

## Top-level functions

### `get_realms(language="english")`

Return all 11 realms as `dict[str, Realm]` keyed by realm code.

### `get_biomes(realm=None, language="english")`

Return biomes as `dict[str, Biome]` keyed by biome code. Pass `realm=` to
restrict to one realm (raises `ValueError` if the realm code is unknown).

### `get_groups(realm=None, biome=None, language="english")`

Return functional groups as `dict[str, FunctionalGroup]`. If `biome=` is
provided without `realm=`, the realm is inferred from the biome code's
leading letters. Raises `ValueError` if the biome is not found in the
inferred or supplied realm.

### `open_ecosystem_map(data, *, engine=None, **kwargs)`

Open an ecosystem map. With `engine=None` (the default), registered
backends are tried in priority order; the first whose `guess_can_open(data)`
returns `True` is used.

### `list_engines()`

Return the registry of available backends as
`dict[str, type[EcosystemBackendEntrypoint]]`.

## Data classes

### `Typology`

See [](typology.md) for the full guide.

Constructor parameters:

| Parameter | Type | Description |
|---|---|---|
| `language` | `str` | One of `"english"` (default), `"spanish"`, `"french"`. |
| `realms` | `dict[str, Realm]` | Override the bundled data. Rarely needed. |
| `ecosystems` | `pandas.DataFrame` | Optional ecosystem records to attach. |
| `ecosystems_functional_group_column` | `str` | Column or index level mapping each ecosystem to a GET EFG code. Required if `ecosystems` is provided. |
| `ecosystems_column` | `str` | Column with the ecosystem type code (e.g., `ECO_CODE`). Required if `ecosystems` is provided. |
| `ecosystem_name_column` | `str` | Optional column with human-readable ecosystem names. |

Methods:

- `get_biomes(realm=None)` — same semantics as the top-level helper.
- `get_groups(realm=None, biome=None)` — same semantics as the top-level helper.
- `add_ecosystems(data, functional_group_column, ecosystems_column, ecosystem_name_column=None)` — attach ecosystem records after construction.
- `to_html(...)` — render the hierarchical table. See [](typology.md#html-display).

Properties:

- `dataframe` — pandas `DataFrame` of the typology (right-joined with attached ecosystems when present).

### `Realm`

| Attribute | Type | Description |
|---|---|---|
| `code` | `str` | E.g., `"T"`, `"M"`, `"MT"`. |
| `name` | `str` | Localized realm name. |
| `description` | `str` | Detailed description. |
| `transitional` | `bool` | `True` for the 6 transitional realms. |
| `url` | `str` | Link on global-ecosystems.org. |
| `biomes` | `dict[str, Biome]` | Child biomes keyed by code. |

### `Biome`

| Attribute | Type | Description |
|---|---|---|
| `code` | `str` | E.g., `"T1"`, `"M2"`. |
| `name` / `description` / `url` | `str` | Localized fields. |
| `functional_groups` | `dict[str, FunctionalGroup]` | Child EFGs keyed by code. |
| `realm_code` | `str` | Parent realm code. |

### `FunctionalGroup`

| Attribute | Type | Description |
|---|---|---|
| `code` | `str` | E.g., `"T1.1"`. |
| `name` / `description` / `url` | `str` | Localized fields. |
| `biome_code` | `str` | Parent biome code. |
| `realm_code` | `str` | Parent realm code. |

## Ecosystem map classes

See [](backends.md) for the backend API. The user-facing classes are:

- `EcosystemMap` — base class.
- `VectorMap` — for vector backends (`parquet`, `shapefile`, `ee_vector`).
- `RasterMap` — for raster backends (`cog`, `ee_raster`).
