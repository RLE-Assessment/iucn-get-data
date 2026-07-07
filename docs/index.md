---
title: iucn-get-data
description: Python tools for the IUCN Global Ecosystem Typology (GET).
kernelspec:
  name: python3
  display_name: 'Python 3'
---

# iucn-get-data

```{code-cell}
---
tags: [remove-cell]
---
from iucn_get_data import Typology, get_realms, get_biomes, get_groups

realms_core = {k: v for k, v in get_realms().items() if v.transitional==False}
realms_transitional = {k: v for k, v in get_realms().items() if v.transitional==True}

```



`iucn-get-data` provides Python access to the upper three levels of the
[IUCN Global Ecosystem Typology (GET) 2.0](https://global-ecosystems.org/):

- **{eval}`len(get_realms())` Realms** (Level 1) — {eval}`len(realms_core)` core + {eval}`len(realms_transitional)` transitional
- **{eval}`len(get_biomes())` Biomes** (Level 2)
- **{eval}`len(get_groups())` Ecosystem Functional Groups** (Level 3)


## What's inside

::::{grid} 1 1 2 2

:::{card} Installation
:link: installation.md

Install from PyPI or directly from GitHub.
:::

:::{card} Quickstart
:link: quickstart.md

Navigate the realm → biome → functional group hierarchy.
:::

:::{card} Typology guide
:link: typology.md

Work with `Typology`, `Realm`, `Biome`, and `FunctionalGroup`.
:::


:::{card} API reference
:link: api.md

Function and class signatures.
:::

:::{card} Data source
:link: data-source.md

Provenance and citation for GET 2.0 data.
:::

::::

## Glossary

```{glossary}
Realm
: Level 1 of GET — the highest classification distinguished by major
  environmental drivers (e.g., Terrestrial, Marine, Freshwater, Subterranean).

Biome
: Level 2 of GET — components of realms united by broad ecosystem structure
  and one or more major ecological drivers.

Ecosystem Functional Group
: Level 3 of GET — groups of related ecosystems within a biome that share
  common ecological drivers, traits, and assembly processes. Often
  abbreviated EFG.
```
