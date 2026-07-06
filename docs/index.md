---
title: iucn-get-data
description: Python tools for the IUCN Global Ecosystem Typology (GET).
---

# iucn-get-data

`iucn-get-data` provides Python access to the upper three levels of the
[IUCN Global Ecosystem Typology (GET) 2.0](https://global-ecosystems.org/):

- **11 Realms** (Level 1) — 5 core + 6 transitional
- **25 Biomes** (Level 2)
- **110 Ecosystem Functional Groups** (Level 3)

It also provides a pluggable {term}`ecosystem map` interface for loading
ecosystem datasets from Parquet, Cloud-Optimized GeoTIFFs, Shapefiles, and
Google Earth Engine assets, and merging them with the typology.

:::{card} Get started in two lines
:link: quickstart.md

```python
from iucn_get_data import Typology
print(Typology())
```
:::

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

:::{card} Ecosystem maps
:link: ecosystem-maps.md

Load Parquet, COG, Shapefile, or Earth Engine ecosystem maps.
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

ecosystem map
: A spatial dataset (vector or raster) whose features or pixels are mapped
  to GET functional groups.
```
