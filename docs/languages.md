---
title: Languages
kernelspec:
  name: python3
  display_name: Python 3
---

# Languages

The package bundles the GET typology as a single SKOS / JSON-LD source
vocabulary that stores all languages together as language-tagged literals. Every
public function and constructor that loads typology data accepts a `language=`
keyword argument selecting which language's labels to return:

| Language | `language=` value |
|---|---|
| English (default) | `"english"` |
| Spanish | `"spanish"` |
| French | `"french"` |

```python
from iucn_get_data import Typology, get_realms, get_biomes, get_groups

Typology(language="spanish")
get_realms(language="french")
get_biomes(realm="T", language="spanish")
get_groups(biome="M1", language="french")
```

Codes (e.g., `T`, `M1`, `T1.1`) are stable across languages — only `name` and
`description` change, and only where a translation exists in the vocabulary:

```{code-cell} python
from iucn_get_data import Typology

biome_en = Typology(language="english").realms["M"].biomes["M1"].name
biome_es = Typology(language="spanish").realms["M"].biomes["M1"].name
biome_en, biome_es
```

## Coverage: which labels are translated

In the current vocabulary, **Biome** names/definitions and the descriptive EFG
properties carry English / Spanish / French text, but **Realm** and **Ecosystem
Functional Group** `prefLabel`s are English-only. A request for a missing
translation falls back to English:

```{code-cell} python
en = Typology(language="english")
es = Typology(language="spanish")

# Realm names are English-only, so Spanish falls back to English.
{"realm_en": en.realms["T"].name, "realm_es": es.realms["T"].name}
```

## Language-tagged literals in the source vocabulary

To read labels per language straight from the RDF graph, load the vocabulary and
inspect the language tag rdflib keeps on each `Literal`
(see [](typology.md#reading-the-source-vocabulary-directly)):

```{code-cell} python
from rdflib import Literal
from rdflib.namespace import SKOS

from iucn_get_data import load_vocabulary

graph = load_vocabulary()
LANGUAGES = {"en": "English", "es": "Español", "fr": "Français"}

# Look up F1.1 (Permanent upland streams) by its skos:notation.
concept = graph.value(predicate=SKOS.notation, object=Literal("F1.1"))


def by_language(concept, prop):
    """Map each language name to the value of `prop`, or None if untranslated."""
    values = {obj.language: str(obj) for obj in graph.objects(concept, prop)}
    return {name: values.get(code) for code, name in LANGUAGES.items()}


for prop_name, prop in [("prefLabel", SKOS.prefLabel), ("note", SKOS.note)]:
    print(prop_name)
    for lang, text in by_language(concept, prop).items():
        snippet = (text[:70] + "…") if text else "(not translated)"
        print(f"  {lang:9}{snippet}")
```

The `note` property is fully translated, while the EFG `prefLabel` is
English-only — the reason Spanish/French EFG names fall back to English above.

## Adding or completing a language

Languages come from the source vocabulary, not from the package. To add a new
language, or to fill the English-only gaps (Realm and EFG names), the upstream
IUCN GET JSON-LD must supply the language-tagged literals. A new export is then
dropped into `data/vocabulary/` and registered in `manifest.yaml` — no code
changes are needed.
