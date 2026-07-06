---
kernelspec:
  name: python3
  display_name: 'Python 3'
---

# iucn-get-data

Tools for working with IUCN Global Ecosystem Typology (GET) data for levels 1 (Realms), 2 (Biomes), and 3 (Functional Groups).

## Installation

```bash
pip install iucn-get-data
```

## Usage

```{code-cell}
from pprint import pprint
from IPython.display import JSON

from iucn_get_data import Typology, get_realms, get_biomes, get_groups
```

### Create a Typology instance

:::{div}
:class: scrollable-output
```{code-cell}
typology = Typology()
typology
```
:::

### Iterate through the hierarchy

:::{div}
:class: scrollable-output
```{code-cell}
for code, realm in typology.realms.items():
    print(f"{code}: {realm.name}")
    for biome_code, biome in realm.biomes.items():
        print(f"  - {biome_code}: {biome.name}")
```
:::

### Realms

Get all realms

```{code-cell}
realms = get_realms()
```

Count the realms:

```{code-cell}
print(f'{len(realms) = }')
```

Print the realms:

```{code-cell}
from IPython.display import display
for r in realms.values():
    print(r)
```

Display as an interactive tree:

```{code-cell}
JSON({code: realm._repr_json_() for code, realm in realms.items()})
```


Select and display a single `Realm`:

```{code-cell}
realms['T']
```

#### Core vs. Transitional Realms

```{code-cell}
realms_core = {k: v for k, v in realms.items() if v.transitional==True}

from IPython.display import display
for r in realms_core.values():
    print(r)
```

```{code-cell}
realms_transitional = {k: v for k, v in realms.items() if v.transitional==False}
for r in realms_transitional.values():
    print(r)
```


Display a single realm.

```{code-cell}
print(realms['T'])
```


### Biomes

Get all biomes

```{code-cell}
biomes = get_biomes()

print(f'{len(biomes) = }')
for r in biomes.values():
    print(r)
```

#### Get biomes from a specific realm

```{code-cell}
terrestrial_biomes = get_biomes(realm='T')

print(f'{len(terrestrial_biomes) = }')
for r in terrestrial_biomes.values():
    print(r)
```

### Functional Groups

Get all functional groups

```{code-cell}
all_groups = get_groups()
print(f'{len(all_groups) = }')
print(f'{all_groups = }')
```

#### Get functional groups from a specific realm

```{code-cell}
terrestrial_groups = get_groups(realm='T')
print(f'{len(terrestrial_groups) = }')
print(f'{terrestrial_groups = }')
```

#### Get functional groups from a specific biome

```{code-cell}
t1_groups = get_groups(biome='T1')
print(f'{len(t1_groups) = }')
print(f'{t1_groups = }')
```

```{code-cell}
m1_groups = get_groups(biome='M1')
print(f'{len(m1_groups) = }')
print(f'{m1_groups = }')
```

## Language Support

The typology ships as a single SKOS / JSON-LD source vocabulary that stores all
languages together. Every loader accepts a `language=` argument — `"english"`
(default), `"spanish"`, or `"french"`:

```{code-cell}
typology_en = Typology()                   # English (default)
typology_es = Typology(language="spanish") # Spanish
typology_fr = Typology(language="french")  # French

# Extract the name of Biome T1
t1_name_en = typology_en.realms['T'].biomes['T1'].name
t1_name_es = typology_es.realms['T'].biomes['T1'].name
t1_name_fr = typology_fr.realms['T'].biomes['T1'].name

print(f'{t1_name_en = }')
print(f'{t1_name_es = }')
print(f'{t1_name_fr = }')
```


### Helper functions also support language parameter

:::{div}
:class: scrollable-output
```{code-cell}
realms_es = get_realms(language="spanish")
pprint(realms_es)
```
:::

:::{note}
In the current vocabulary (`iucn-get_2026-04-01-v3`), Biome names/definitions and the descriptive EFG properties are translated, while Realm and Ecosystem Functional Group names are English-only; missing translations fall back to English.
:::

## Data Structure

The package includes data for:

- **{eval}`len(get_realms())` Realms** ({eval}`len(realms_core)` core + {eval}`len(realms_transitional)` transitional)
- **25 Biomes**
- **110 Functional Groups**

## Development

Install with dev dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

## Project Structure

```
iucn-get-data/
├── src/
│   └── iucn_get_data/
│       ├── __init__.py
│       ├── core.py            # Typology, Realm, Biome, FunctionalGroup
│       ├── vocabulary.py      # loads the JSON-LD source of truth
│       ├── ecosystem_map.py
│       ├── examples.py
│       ├── backends/          # data backends (parquet, COG, Earth Engine, shapefile)
│       └── data/
│           ├── map_style.yaml
│           └── vocabulary/
│               ├── iucn-get_2026-04-01-v3.jsonld  # SKOS controlled vocabulary
│               └── manifest.yaml                  # version registry
├── tests/
│   ├── __init__.py
│   └── test_core.py
└── pyproject.toml
```

## Package Names

- **PyPI/pip name**: `iucn-get-data` (install with `pip install iucn-get-data`)
- **Import name**: `iucn_get_data` (import with `from iucn_get_data import ...`)

## Data Source

Data is based on the IUCN Global Ecosystem Typology v2:
- Global Ecosystem Typology Website: https://global-ecosystems.org/
- Controlled vocabularies: https://demo.vocabs.ardc.edu.au/viewById/1167
