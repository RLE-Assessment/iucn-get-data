---
title: Contributing
---

# Contributing

## Dev setup

```bash
git clone https://github.com/RLE-Assessment/iucn-get-data
cd iucn-get-data
pip install -e ".[dev]"
```

## Running tests

```bash
pytest
```

The suite covers core typology loading and the vocabulary parser.

## Building these docs

The documentation in `docs/` is written for [MyST](https://mystmd.org/).
Install the CLI and preview locally:

```bash
npm install -g mystmd
cd docs
myst start          # live preview at http://localhost:3000
myst build --html   # static HTML in _build/html/
```

## Layout

```
docs/
├── myst.yml             # MyST project config + TOC
├── index.md             # landing page
├── installation.md
├── quickstart.md
├── typology.md
├── languages.md
├── api.md
├── data-source.md
└── contributing.md
```

## Style

- Keep code samples runnable against the current `main` branch.
- Use MyST cross-references (`[](page.md#anchor)`) rather than raw URLs
  for in-repo links — they get checked at build time.
