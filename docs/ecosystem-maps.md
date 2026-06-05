---
title: Ecosystem maps
---

# Ecosystem maps

An *ecosystem map* is a spatial dataset (vector or raster) where features
or pixels are mapped to GET functional groups. `iucn-get-data` provides a
pluggable backend system to load such datasets and align them with the
typology.

## Opening a map

```python
from iucn_get_data import open_ecosystem_map

emap = open_ecosystem_map("colombia.parquet")
```

`open_ecosystem_map` auto-detects the backend from the input. You can
force a backend with `engine=`:

```python
emap = open_ecosystem_map("ecosystems/", engine="shapefile")
emap = open_ecosystem_map("gs://bucket/global.tif", engine="cog")
```

Remote `gs://` and `https://` paths are downloaded once to
`/tmp/iucn_get_data_cache/` and reused across calls.

## Built-in backends

The following backends ship with the package and are registered via the
`iucn_get_data.ecosystem_backends` entry-point group:

| Engine name | Class | Input |
|---|---|---|
| `parquet` | `ParquetBackend` | Parquet file with a functional-group column |
| `cog` | `CogBackend` | Cloud-Optimized GeoTIFF |
| `shapefile` | `ShapefileBackend` | Shapefile (`.shp` or zipped) |
| `ee_vector` | `EEVectorBackend` | Earth Engine `FeatureCollection` or asset ID |
| `ee_raster` | `EERasterBackend` | Earth Engine `Image` or asset ID |

See [](backends.md) for the full backend reference, including the
abstract base class third parties extend to register new backends.

## Class hierarchy

Backends return instances of one of three classes:

- `EcosystemMap` — base class with shared Jupyter display
- `VectorMap` — intermediate for vector backends (GET column attributes,
  HTML preview)
- `RasterMap` — intermediate for raster backends (band / dataframe
  attributes, HTML preview)

All concrete backend classes inherit from `VectorMap` or `RasterMap`.

## Listing engines

```python
from iucn_get_data import list_engines

list_engines()
# {'parquet': ParquetBackend, 'cog': CogBackend, ...}
```

## Example notebooks

The repository's `examples/` directory contains runnable notebooks:

- `examples/load_parquet.ipynb`
- `examples/load_gee_vector.ipynb`
- `examples/ecosystem_map_display.ipynb`
