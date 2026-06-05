---
title: Quickstart
---

# Quickstart

This page walks through the most common operations: loading the typology,
filtering by realm or biome, and inspecting functional groups.

## Load the typology

```python
from iucn_get_data import Typology

typology = Typology()
print(len(typology.realms))   # 10
print(typology)               # tree-style text representation
```

In a Jupyter notebook, `typology` renders as an HTML table via
`_repr_html_`. See [](typology.md#html-display) for customization.

## Walk the hierarchy

```python
for code, realm in typology.realms.items():
    print(f"{code}: {realm.name}")
    for biome_code, biome in realm.biomes.items():
        print(f"  - {biome_code}: {biome.name}")
        for fg_code, fg in biome.functional_groups.items():
            print(f"      • {fg_code}: {fg.name}")
```

## Top-level helpers

For one-off lookups, the package provides module-level helpers that return
plain dictionaries:

```python
from iucn_get_data import get_realms, get_biomes, get_groups

get_realms()                        # 10 Realms
get_biomes()                        # 25 Biomes
get_biomes(realm="T")               # 7 Terrestrial biomes
get_groups(biome="T1")              # 4 EFGs in biome T1
get_groups(realm="T", biome="T1")   # equivalent — realm inferred from biome
```

:::{tip}
The biome code's leading letters are the realm code. If you pass `biome="T1"`,
you can omit `realm`; the helpers infer it.
:::

## Languages

The typology data ships in English (default), Spanish, and French:

```python
es = Typology(language="spanish")
es.realms["T"].name  # "Terrestre"

get_realms(language="spanish")
```

See [](languages.md) for the full list of language-aware functions.

## Next steps

- Attach an ecosystem dataset and render a merged table → [](typology.md#attaching-ecosystems)
- Load a spatial ecosystem map → [](ecosystem-maps.md)
- See every public function → [](api.md)
