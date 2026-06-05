---
title: Languages
---

# Languages

The package bundles GET 2.0 data in three languages:

| Language code | File |
|---|---|
| `english` (default) | `data/english.yaml` |
| `spanish` | `data/spanish.yaml` |
| `french` | `data/french.yaml` |

Every public function and constructor that loads typology data accepts a
`language=` keyword argument:

```python
from iucn_get_data import Typology, get_realms, get_biomes, get_groups

Typology(language="spanish")
get_realms(language="french")
get_biomes(realm="T", language="spanish")
get_groups(biome="M1", language="french")
```

Codes (e.g., `T`, `M1`, `T1.1`) are stable across languages — only `name`
and `description` change.

```python
Typology(language="english").realms["T"].name   # "Terrestrial"
Typology(language="spanish").realms["T"].name   # "Terrestre"
```

## Adding a language

The YAML files live in `src/iucn_get_data/data/`. To add a translation,
add a new file (e.g., `portuguese.yaml`) mirroring the structure of
`english.yaml` and pass `language="portuguese"`.
