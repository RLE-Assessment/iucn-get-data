# iucn-get-data

Tools for working with IUCN Global Ecosystem Typology (GET) data for levels 1 (Realms), 2 (Biomes), and 3 (Functional Groups).

## Installation

```bash
pip install iucn-get-data
```

## Usage

```python
from iucn_get_data import Typology, get_realms, get_biomes, get_groups

# Create a Typology instance
typology = Typology()
print(len(typology.realms))  # 10

# Navigate the hierarchy
for code, realm in typology.realms.items():
    print(f"{code}: {realm.name}")
    for biome_code, biome in realm.biomes.items():
        print(f"  - {biome_code}: {biome.name}")

# Get all realms (10 total: 4 core + 6 transitional)
realms = get_realms()

# Get all biomes (25 total)
all_biomes = get_biomes()

# Get biomes from a specific realm
terrestrial_biomes = get_biomes(realm='T')  # 7 biomes
marine_biomes = get_biomes(realm='M')       # 4 biomes

# Get all functional groups (109 total)
all_groups = get_groups()

# Get functional groups from a specific realm
terrestrial_groups = get_groups(realm='T')  # 34 groups

# Get functional groups from a specific biome
t1_groups = get_groups(biome='T1')          # 4 groups
m1_groups = get_groups(biome='M1')          # 10 groups

# Combined filters
t1_groups = get_groups(realm='T', biome='T1')
```

## Language Support

The package includes data in English (default) and Spanish:

```python
from iucn_get_data import Typology

# English (default)
typology_en = Typology()
print(typology_en.realms['T'].name)  # "Terrestrial"

# Spanish
typology_es = Typology(language="spanish")
print(typology_es.realms['T'].name)  # "Terrestre"

# Helper functions also support language parameter
realms_es = get_realms(language="spanish")
```

## Data Structure

The package includes data for:

- **10 Realms** (4 core + 6 transitional)
  - Core: Terrestrial (T), Marine (M), Freshwater (F), Subterranean (S)
  - Transitional: TF, FM, MFT, MT, SF, SM
- **25 Biomes**
- **109 Functional Groups**

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
│       ├── main.py
│       ├── examples.py
│       └── data/
│           ├── english.yaml
│           └── spanish.yaml
├── tests/
│   ├── __init__.py
│   └── test_main.py
└── pyproject.toml
```

## Package Names

- **PyPI/pip name**: `iucn-get-data` (install with `pip install iucn-get-data`)
- **Import name**: `iucn_get_data` (import with `from iucn_get_data import ...`)

## Data Source

Data is based on the IUCN Global Ecosystem Typology v2.0:
- https://global-ecosystems.org/
- https://zenodo.org/records/10081251
