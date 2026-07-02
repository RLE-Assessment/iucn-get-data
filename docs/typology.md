---
title: The Typology guide
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

`Typology` reads the bundled per-language YAML. If you instead want the
*source* IUCN GET vocabulary — the SKOS-encoded JSON-LD (or Turtle) export
distributed with the package — parse it with
[rdflib](https://rdflib.readthedocs.io/), which is a dependency of this
package and reads both formats (switch `format="json-ld"` to
`format="turtle"`). This exposes the raw `Realm` / `Biome` /
`EcosystemFunctionalGroup` concepts, their `skos:notation` codes, the
hierarchy (`skos:broader`), and multilingual descriptions.

```python
import pandas as pd
from rdflib import Graph, Namespace, RDF
from rdflib.namespace import SKOS

# IUCN GET ontology namespace (the Realm/Biome/EFG classes and code properties).
GETO = Namespace("https://w3id.org/iucn-get/ontology#")

datafile = "src/iucn_get_data/data/ands-nc_iucn-get-example_2026-04-01-v3.jsonld"
graph = Graph().parse(datafile, format="json-ld")

# The three GET ontology classes, in hierarchy order, with their code property.
GET_CLASSES = [
    ("Realm", 1, GETO.realmCode),
    ("Biome", 2, GETO.biomeCode),
    ("EcosystemFunctionalGroup", 3, GETO.efgCode),
]


def classify(concept):
    """Return (get_class, level, code) from a concept's GET rdf:type."""
    for name, level, code_prop in GET_CLASSES:
        if (concept, RDF.type, GETO[name]) in graph:
            return name, level, graph.value(concept, code_prop)
    return None, None, None


rows = []
for concept in graph.subjects(RDF.type, SKOS.Concept):
    get_class, level, _code = classify(concept)
    rows.append({
        "notation": str(graph.value(concept, SKOS.notation)),
        "pref_label": str(graph.value(concept, SKOS.prefLabel)),
        "get_class": get_class,
        "level": level,
        "broader": graph.value(concept, SKOS.broader),
    })

df = pd.DataFrame(rows).sort_values(["level", "notation"]).reset_index(drop=True)
df["get_class"].value_counts()
```

This yields one row per `skos:Concept`:

```text
EcosystemFunctionalGroup    110
Biome                        25
Realm                        11
```

The demo export bundled here carries 11 realms / 25 biomes / 110 EFGs; the
packaged YAML exposes the stable 10 / 25 / 109 subset (see
[](data-source.md#coverage)). The vocabulary is aspatial — join the
`notation` column to a mapped ecosystem layer (GeoParquet, Earth Engine, …)
to give the concepts geometry.
