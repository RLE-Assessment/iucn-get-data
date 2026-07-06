---
title: The Typology guide
kernelspec:
  name: python3
  display_name: Python 3
---

# The Typology guide

The `Typology` class is the main entry point. It loads the bundled GET 2.0
data for the chosen language and exposes a nested dictionary of `Realm` →
`Biome` → `FunctionalGroup` objects.

## Construction

```python
from iucn_get_data import Typology

typology = Typology()                  # English (default)
typology = Typology(language="spanish")
```

All `Typology(...)` instances are independent — modifying one does not affect
another.

## Filtering

`Typology` provides `get_biomes` and `get_groups` methods that mirror the
module-level helpers but operate on the already-loaded data, avoiding a
second YAML read:

```python
typology.get_biomes(realm="T")
typology.get_groups(biome="M1")
```

Invalid codes raise `ValueError` listing the valid options.

## Attaching ecosystems

You can attach a pandas DataFrame of ecosystem records to the typology so
the two can be navigated and displayed together:

```python
import pandas as pd
from iucn_get_data import Typology

ecosystems = pd.DataFrame({
    "ECO_CODE": ["E1", "E2", "E3"],
    "EFG1":     ["T1.1", "T1.1", "M1.1"],
    "ECO_NAME": ["Lowland rainforest A", "Lowland rainforest B", "Reef A"],
})

typology = Typology()
typology.add_ecosystems(
    ecosystems,
    functional_group_column="EFG1",
    ecosystems_column="ECO_CODE",
    ecosystem_name_column="ECO_NAME",
)
```

Equivalently, pass these at construction time:

```python
typology = Typology(
    ecosystems=ecosystems,
    ecosystems_functional_group_column="EFG1",
    ecosystems_column="ECO_CODE",
    ecosystem_name_column="ECO_NAME",
)
```

Either form validates that the column names exist in the DataFrame's
columns or index.

### Merged DataFrame

`typology.dataframe` returns a pandas DataFrame. With no ecosystems
attached, it lists every functional group indexed by
`(realm_code, biome_code, functional_group_code)`. With ecosystems
attached, it returns the right-join of typology and ecosystem rows so
every input ecosystem is preserved.

### Tree text representation

`print(typology)` produces a tree-style text dump. When ecosystems are
attached, branches without ecosystems are pruned automatically.

```text
T: Terrestrial
  └─ T1: Tropical-subtropical forests
      └─ T1.1: Tropical/subtropical lowland rainforests
          └─ E1: Lowland rainforest A
          └─ E2: Lowland rainforest B
M: Marine
  └─ M1: Marine shelf
      └─ M1.1: Seagrass meadows
          └─ E3: Reef A
```

## HTML display

In Jupyter, the default `_repr_html_` renders a hierarchical table. Call
`Typology.to_html` directly to customize:

```python
typology.to_html(
    ecosystem_columns=["ECO_CODE", "ECO_NAME"],
    drop_columns=["description"],
    hide_empty=True,
)
```

| Parameter | Effect |
|---|---|
| `ecosystem_columns` | Restrict columns shown for ecosystem rows. |
| `drop_columns` | Exclude specific columns from the display. |
| `hide_empty` | Hide realms/biomes/EFGs with no attached ecosystems. Defaults to `True` when ecosystems are attached, `False` otherwise. |
| `ecosystem_name_column` / `ecosystem_id_column` | Promote a name/ID column to the leftmost positions. |

## Data classes

`Realm`, `Biome`, and `FunctionalGroup` are simple `dataclass` types — see
[](api.md#data-classes) for their attributes.

## Reading the source vocabulary directly

`Typology` (above) is built from the bundled IUCN GET **source vocabulary** — a
single SKOS-encoded JSON-LD file that is the package's source of truth. To work
with the raw RDF graph yourself, call `load_vocabulary()`, which returns a parsed
[rdflib](https://rdflib.readthedocs.io/) `Graph`. It reads the bundled file today
and can fetch a future CDN-hosted version transparently — the call is unchanged
either way. The graph exposes the raw `Realm` / `Biome` /
`EcosystemFunctionalGroup` concepts, their `skos:notation` codes, the hierarchy
(`skos:broader`), and multilingual labels.

```{code-cell} python
import pandas as pd
from rdflib import RDF
from rdflib.namespace import SKOS

from iucn_get_data import load_vocabulary
from iucn_get_data.vocabulary import GETO  # IUCN GET ontology namespace

graph = load_vocabulary()

# The three GET ontology classes, in hierarchy order.
GET_CLASSES = ["Realm", "Biome", "EcosystemFunctionalGroup"]


def classify(concept):
    """Return (get_class, level) from a concept's GET rdf:type."""
    for level, name in enumerate(GET_CLASSES, start=1):
        if (concept, RDF.type, GETO[name]) in graph:
            return name, level
    return None, None


rows = []
for concept in graph.subjects(RDF.type, SKOS.Concept):
    get_class, level = classify(concept)
    rows.append({
        "notation": str(graph.value(concept, SKOS.notation)),
        "pref_label": str(graph.value(concept, SKOS.prefLabel)),
        "get_class": get_class,
        "level": level,
    })

df = pd.DataFrame(rows).sort_values(["level", "notation"]).reset_index(drop=True)
df["get_class"].value_counts()
```

The vocabulary holds 11 realms, 25 biomes, and 110 EFGs. It is aspatial — join
the `notation` column to a mapped ecosystem layer (GeoParquet, Earth Engine, …)
to give the concepts geometry.
