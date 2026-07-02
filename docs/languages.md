---
title: Languages
---

# Languages

The package bundles GET 2.0 data in three languages:

| Language code | File |
|---|---|
| `english` (default) | `data/english.yaml` |
| `spanish` | `data/spanish.yaml` |
| `french` | `data/french.yaml` |

Every public function and constructor that loads typology data accepts a
`language=` keyword argument:

```python
from iucn_get_data import Typology, get_realms, get_biomes, get_groups

Typology(language="spanish")
get_realms(language="french")
get_biomes(realm="T", language="spanish")
get_groups(biome="M1", language="french")
```

Codes (e.g., `T`, `M1`, `T1.1`) are stable across languages — only `name`
and `description` change.

```python
Typology(language="english").realms["T"].name   # "Terrestrial"
Typology(language="spanish").realms["T"].name   # "Terrestre"
```

## Language-tagged literals in the source vocabulary

The bundled YAML is pre-split by language, but the source SKOS vocabulary
(see [](typology.md#reading-the-source-vocabulary-directly)) stores every
language together as language-tagged RDF literals. rdflib keeps the tag on
each `Literal` (`literal.language`), so you can pull a concept's properties
per language straight from the graph:

```python
from rdflib import Literal
from rdflib.namespace import SKOS

LANGUAGES = {"en": "English", "es": "Español", "fr": "Français"}

# Look up F1.1 (Permanent upland streams) by its skos:notation.
concept = graph.value(predicate=SKOS.notation, object=Literal("F1.1"))


def by_language(concept, prop):
    """Map each language code to the value of `prop`, or None if untranslated."""
    values = {obj.language: str(obj) for obj in graph.objects(concept, prop)}
    return {code: values.get(code) for code in LANGUAGES}


by_language(concept, SKOS.note)
```

Not every property is translated. For Ecosystem Functional Groups the
`skos:prefLabel` is English-only, while the descriptive properties
(`skos:note`, `iucn-get:ecologicalDrivers`, `iucn-get:ecosystemProperties`, …)
carry the full English / Spanish / French text:

```text
# prefLabel
  English  Permanent upland streams
  Español  (not translated)
  Français (not translated)

# note
  English  High proportion of global stream length. In steep to moderate terrain …
  Español  Alta proporción de la longitud global de los arroyos. En terrenos …
  Français Forte proportion de la longueur des cours d'eau dans le monde. Sur …
```

## Adding a language

The YAML files live in `src/iucn_get_data/data/`. To add a translation,
add a new file (e.g., `portuguese.yaml`) mirroring the structure of
`english.yaml` and pass `language="portuguese"`.
