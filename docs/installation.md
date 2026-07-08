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

## With uv

Using [uv](https://docs.astral.sh/uv/), add it to a project:

```bash
uv add iucn-get-data
```

Or install it into the current environment:

```bash
uv pip install iucn-get-data
```

From GitHub:

```bash
uv add "iucn-get-data @ git+https://github.com/RLE-Assessment/iucn-get-data"
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

The package ships one optional dependency group:

| Extra | Purpose | Installs |
|---|---|---|
| `dev` | Run the test suite | `pytest` |

Install it with:

```bash
pip install "iucn-get-data[dev]"
```

## Requirements

- Python ≥ 3.11
