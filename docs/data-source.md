---
title: Data source & citation
---

# Data source & citation

The bundled YAML data is derived from the
[IUCN Global Ecosystem Typology (GET) 2.0](https://global-ecosystems.org/).

## Citation

When using this package, cite the underlying typology:

> Keith, D.A., Ferrer-Paris, J.R., Nicholson, E., & Kingsford, R.T. (eds.)
> (2020). *The IUCN Global Ecosystem Typology 2.0: Descriptive profiles for
> Biomes and Ecosystem Functional Groups.* Gland, Switzerland: IUCN.

A persistent dataset record is available on Zenodo:

- <https://zenodo.org/records/10081251>

## Coverage

The package exposes the **upper three levels** of the typology only:

1. **Realms** — 10 (4 core + 6 transitional)
2. **Biomes** — 25
3. **Ecosystem Functional Groups** — 109

The lower three composition-based levels (biogeographic ecotypes, global
ecosystem types, subglobal types) are not bundled. Users typically supply
these themselves and attach them via `Typology.add_ecosystems` — see
[](typology.md#attaching-ecosystems).

## Updates

Each YAML file under `src/iucn_get_data/data/` is the source of truth for
its language. Submit corrections or additions as pull requests; see
[](contributing.md).
