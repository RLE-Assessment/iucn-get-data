---
title: Installation
---

# Installation

## From PyPI

```bash
pip install iucn-get-data
```

## From GitHub

```bash
pip install "iucn-get-data @ git+https://github.com/RLE-Assessment/iucn-get-data"
```

## As a script dependency

`iucn-get-data` works well with [PEP 723](https://peps.python.org/pep-0723/)
script metadata so single-file scripts can declare it inline:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = ["iucn-get-data @ git+https://github.com/RLE-Assessment/iucn-get-data"]
# ///

from iucn_get_data import Typology
print(Typology())
```

## Optional extras

The package ships several optional dependency groups for backends that
require heavier libraries:

| Extra | Purpose | Installs |
|---|---|---|
| `dev` | Run the test suite | `pytest` |
| `ee` | Earth Engine vector/raster backends | `earthengine-api`, `pandas` |
| `cog` | Cloud-Optimized GeoTIFF backend | `rioxarray`, `rasterio` |
| `gcs` | Read Parquet from Google Cloud Storage | `geopandas`, `pyarrow`, `gcsfs`, `pandas` |

Install one or more:

```bash
pip install "iucn-get-data[ee,cog]"
```

## Requirements

- Python ≥ 3.11
