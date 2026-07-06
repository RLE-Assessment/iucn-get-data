---
title: Data source & citation
---

# Data source & citation

The bundled vocabulary is the
[IUCN Global Ecosystem Typology (GET) 2.0](https://global-ecosystems.org/),
distributed as a single SKOS-encoded JSON-LD controlled vocabulary.

## Citation

When using this package, cite the underlying typology:

> Keith, D.A., Ferrer-Paris, J.R., Nicholson, E., & Kingsford, R.T. (eds.)
> (2020). *The IUCN Global Ecosystem Typology 2.0: Descriptive profiles for
> Biomes and Ecosystem Functional Groups.* Gland, Switzerland: IUCN.

A persistent dataset record is available on Zenodo:

- <https://zenodo.org/records/10081251>

## Coverage

The package exposes the **upper three levels** of the typology only:

1. **Realms** — 11 (5 core + 6 transitional)
2. **Biomes** — 25
3. **Ecosystem Functional Groups** — 110

The lower three composition-based levels (biogeographic ecotypes, global
ecosystem types, subglobal types) are not bundled. Users typically supply
these themselves and attach them via `Typology.add_ecosystems` — see
[](typology.md#attaching-ecosystems).

## Updates

The source vocabulary lives under `src/iucn_get_data/data/vocabulary/`: the
JSON-LD file(s) plus a `manifest.yaml` registry that records the available
versions and the current default. A new upstream release is added by dropping
the file in and adding a manifest entry (a version may also point at an external
`url`). Submit corrections or additions as pull requests; see
[](contributing.md).
