---
title: Backends
---

# Backends

Backends are pluggable adapters that turn an input — a file path, URL, or
Earth Engine object — into an `EcosystemMap` instance.

## Built-in backends

| Engine name | Class | Output type | Optional extra |
|---|---|---|---|
| `parquet` | `ParquetBackend` | `VectorMap` | (none) — uses `pandas`/`pyarrow` |
| `shapefile` | `ShapefileBackend` | `VectorMap` | (none) |
| `cog` | `CogBackend` | `RasterMap` | `iucn-get-data[cog]` |
| `ee_vector` | `EEVectorBackend` | `VectorMap` | `iucn-get-data[ee]` |
| `ee_raster` | `EERasterBackend` | `RasterMap` | `iucn-get-data[ee]` |

## Registering a third-party backend

Backends are discovered through the
`iucn_get_data.ecosystem_backends` entry-point group. Declare yours in
`pyproject.toml`:

```toml
[project.entry-points."iucn_get_data.ecosystem_backends"]
my_backend = "my_package.module:MyBackend"
```

…and subclass `EcosystemBackendEntrypoint`:

```python
from iucn_get_data.backends import EcosystemBackendEntrypoint
from iucn_get_data import VectorMap

class MyBackend(EcosystemBackendEntrypoint):
    priority = 50  # lower = tried first

    @classmethod
    def guess_can_open(cls, data) -> bool:
        return isinstance(data, str) and data.endswith(".mine")

    @classmethod
    def open_ecosystem_map(cls, data, **kwargs) -> VectorMap:
        ...  # build and return your VectorMap / RasterMap subclass
```

After installation, `list_engines()` will include the new backend and
`open_ecosystem_map(data)` will dispatch to it automatically when
`guess_can_open` returns `True`.

## Engine resolution

When `engine=None` is passed to `open_ecosystem_map`, engines are sorted
by `priority` (ascending) and the first whose `guess_can_open(data)`
returns `True` is used. When `engine="name"` is passed explicitly, only
that backend is tried (and an error is raised if it cannot open the
input).

## Remote inputs

`open_ecosystem_map` transparently caches remote `gs://` and `https://`
inputs to `/tmp/iucn_get_data_cache/<hash>_<filename>` before passing
them to the backend.

## Refreshing the registry

If you install or remove a backend in the same Python process (e.g.,
during testing), call `iucn_get_data.backends.refresh_engines()` to
clear the discovery cache.
