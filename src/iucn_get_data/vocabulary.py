"""Load the IUCN GET controlled vocabulary (SKOS / JSON-LD) as source of truth.

The bundled vocabulary lives under ``data/vocabulary/`` alongside a
``manifest.yaml`` registry. New versions in the same JSON-LD/SKOS format are
added by dropping the file in and adding a manifest entry (see the manifest
comments). A version may instead point at an external ``url`` (e.g. a CDN),
which is fetched and cached transparently via :func:`_cache_remote_file` —
no code changes needed when the source moves off-disk.

``load_vocabulary()`` returns a parsed :class:`rdflib.Graph`;
``build_realms_from_graph()`` turns that graph into the nested ``Realm`` /
``Biome`` / ``FunctionalGroup`` structure the rest of the package consumes.
"""
from __future__ import annotations

from functools import lru_cache
from importlib import resources

import yaml
from rdflib import Graph, Namespace
from rdflib.namespace import RDF, SKOS

# Namespaces used by the IUCN GET SKOS vocabulary.
GETO = Namespace("https://w3id.org/iucn-get/ontology#")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")

_DATA_PKG = "iucn_get_data"
_VOCAB_DIR = "data/vocabulary"

# Package language names -> BCP-47 tags used for language-tagged literals.
_LANGUAGE_TAGS = {"english": "en", "spanish": "es", "french": "fr"}

# GET ontology classes in hierarchy order: (ontology class name, GET level).
_GET_CLASSES = [("Realm", 1), ("Biome", 2), ("EcosystemFunctionalGroup", 3)]

# global-ecosystems.org browse-URL path segment per level.
_URL_SEGMENT = {1: "realms", 2: "biomes", 3: "groups"}

_REMOTE_PREFIXES = ("http://", "https://", "gs://")


def _manifest() -> dict:
    """Read the bundled vocabulary version manifest."""
    ref = resources.files(_DATA_PKG).joinpath(f"{_VOCAB_DIR}/manifest.yaml")
    return yaml.safe_load(ref.read_text(encoding="utf-8"))


def resolve_source(version: str = "current", source: str | None = None) -> str:
    """Resolve a vocabulary version to a filesystem path or URL.

    ``source`` (an explicit local path or URL) takes precedence. Otherwise the
    manifest is consulted: an entry's ``url`` wins (remote/CDN), else the
    bundled ``file`` is returned as a filesystem path.
    """
    if source is not None:
        return source

    manifest = _manifest()
    if version == "current":
        version = manifest["current"]
    entry = manifest.get("versions", {}).get(version)
    if entry is None:
        available = ", ".join(manifest.get("versions", {})) or "(none)"
        raise ValueError(
            f"Unknown vocabulary version '{version}'. Available: {available}"
        )
    if entry.get("url"):
        return entry["url"]
    ref = resources.files(_DATA_PKG).joinpath(f"{_VOCAB_DIR}/{entry['file']}")
    with resources.as_file(ref) as path:
        return str(path)


@lru_cache(maxsize=None)
def load_vocabulary(version: str = "current", source: str | None = None) -> Graph:
    """Return the controlled vocabulary as a parsed :class:`rdflib.Graph`.

    Results are cached: the graph is parsed once and reused. Remote sources
    (``https://``/``gs://``) are downloaded and cached locally first.

    Args:
        version: Manifest version id, or ``"current"`` (default).
        source: Explicit path or URL, bypassing the manifest.
    """
    manifest = None if source is not None else _manifest()
    fmt = "json-ld"
    if manifest is not None:
        v = manifest["current"] if version == "current" else version
        entry = manifest.get("versions", {}).get(v)
        if entry is None:
            available = ", ".join(manifest.get("versions", {})) or "(none)"
            raise ValueError(
                f"Unknown vocabulary version '{v}'. Available: {available}"
            )
        fmt = entry.get("format", "json-ld")

    location = resolve_source(version=version, source=source)
    graph = Graph()
    if location.startswith(_REMOTE_PREFIXES):
        graph.parse(_cache_remote_file(location), format=fmt)
    else:
        graph.parse(location, format=fmt)
    return graph


def _cache_remote_file(data: str) -> str:
    """Download a remote file to a local cache and return the local path.

    Supports gs:// and https:// URIs.  If the file is already cached,
    returns the cached path without re-downloading.  Non-remote paths
    are returned unchanged.
    """
    if not isinstance(data, str):
        return data
    if not (data.startswith("gs://") or data.startswith("https://")):
        return data

    import hashlib
    import logging
    from pathlib import Path

    logger = logging.getLogger(__name__)

    cache_dir = Path("/tmp/iucn_get_data_cache")
    cache_dir.mkdir(parents=True, exist_ok=True)

    url_hash = hashlib.sha256(data.encode()).hexdigest()[:12]
    # Preserve the original filename for readability
    filename = data.rstrip("/").rsplit("/", 1)[-1]
    cache_path = cache_dir / f"{url_hash}_{filename}"

    if cache_path.exists():
        logger.info("Using cached file: %s", cache_path)
        return str(cache_path)

    import fsspec

    logger.info("Downloading %s to %s", data, cache_path)
    fs, fpath = fsspec.core.url_to_fs(data)
    fs.get(fpath, str(cache_path))
    return str(cache_path)


# Alias for callers that prefer the lower-level name.
load_graph = load_vocabulary


def _lang_value(graph, subject, prop, tag, fallback="en") -> str:
    """First literal for ``prop`` in language ``tag``, falling back to English.

    Realm and EFG labels/definitions are English-only in the current
    vocabulary, so non-English requests fall back to ``en`` (then to any
    available value).
    """
    values = {}
    for obj in graph.objects(subject, prop):
        values.setdefault(getattr(obj, "language", None), str(obj))
    for key in (tag, fallback, None):
        if key in values:
            return values[key]
    return next(iter(values.values()), "")


def _name(graph, subject, tag, cls_name) -> str:
    """Preferred label, with the redundant class suffix (" biome") removed."""
    label = _lang_value(graph, subject, SKOS.prefLabel, tag)
    suffix = f" {cls_name.lower()}"  # e.g. Biome labels end with " biome"
    if label.lower().endswith(suffix):
        label = label[: -len(suffix)]
    return label


def _description(graph, subject, tag) -> str:
    """Definition in the requested language, else the (English) scope note."""
    return _lang_value(graph, subject, SKOS.definition, tag) or _lang_value(
        graph, subject, SKOS.scopeNote, tag
    )


def _url(graph, subject, level, code) -> str:
    """Non-localized browse URL from foaf:page, else synthesized from the code."""
    for obj in graph.objects(subject, FOAF.page):
        page = str(obj)
        if "/es/" not in page and "/fr/" not in page:
            return page
    return f"https://global-ecosystems.org/explore/{_URL_SEGMENT[level]}/{code}"


def _transitional(graph, subject) -> bool:
    realm_type = graph.value(subject, GETO.realmType)
    return realm_type is not None and str(realm_type) == "transitional"


def build_realms_from_graph(graph: Graph, language: str = "english") -> dict:
    """Build the nested ``{code: Realm}`` structure from a vocabulary graph.

    Realms contain Biomes contain FunctionalGroups, mirroring the previous
    YAML-derived structure. Names/descriptions are taken in ``language`` with
    English fallback where a translation is absent.
    """
    from .core import Biome, FunctionalGroup, Realm, _natural_sort_key

    tag = _LANGUAGE_TAGS.get(language, "en")

    # Gather every concept up front, keyed by its IRI.
    concepts = {}
    for cls_name, level in _GET_CLASSES:
        for subject in graph.subjects(RDF.type, GETO[cls_name]):
            broader = graph.value(subject, SKOS.broader)
            concepts[str(subject)] = {
                "iri": subject,
                "level": level,
                "cls": cls_name,
                "code": str(graph.value(subject, SKOS.notation)),
                "name": _name(graph, subject, tag, cls_name),
                "description": _description(graph, subject, tag),
                "url": _url(graph, subject, level, str(graph.value(subject, SKOS.notation))),
                "broader": str(broader) if broader is not None else None,
            }

    def code_of(iri):
        entry = concepts.get(iri)
        return entry["code"] if entry else None

    realms, biomes = {}, {}

    for c in concepts.values():
        if c["level"] == 1:
            realms[c["code"]] = Realm(
                code=c["code"],
                name=c["name"],
                description=c["description"],
                transitional=_transitional(graph, c["iri"]),
                url=c["url"],
                biomes={},
            )

    for c in concepts.values():
        if c["level"] == 2:
            realm_code = code_of(c["broader"])
            biome = Biome(
                code=c["code"],
                name=c["name"],
                description=c["description"],
                url=c["url"],
                functional_groups={},
                realm_code=realm_code,
            )
            biomes[c["code"]] = biome
            if realm_code in realms:
                realms[realm_code].biomes[c["code"]] = biome

    for c in concepts.values():
        if c["level"] == 3:
            biome_code = code_of(c["broader"])
            parent = biomes.get(biome_code)
            fg = FunctionalGroup(
                code=c["code"],
                name=c["name"],
                description=c["description"],
                url=c["url"],
                biome_code=biome_code,
                realm_code=parent.realm_code if parent else None,
            )
            if parent is not None:
                parent.functional_groups[fg.code] = fg

    # Sort every level naturally by code for stable, predictable ordering.
    def sort_dict(d):
        return dict(sorted(d.items(), key=lambda kv: _natural_sort_key(kv[0])))

    realms = sort_dict(realms)
    for realm in realms.values():
        realm.biomes = sort_dict(realm.biomes)
        for biome in realm.biomes.values():
            biome.functional_groups = sort_dict(biome.functional_groups)
    return realms
