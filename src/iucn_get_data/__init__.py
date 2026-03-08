"""IUCN Get Data - Tools for working with IUCN Global Ecosystem Typology data."""

from importlib.metadata import version

from .core import (
    get_realms, get_biomes, get_groups,
    Typology, Realm, Biome, FunctionalGroup
)

__version__ = version("iucn-get-data")
__all__ = [
    'get_realms', 'get_biomes', 'get_groups',
    'Typology', 'Realm', 'Biome', 'FunctionalGroup',
    'EcosystemMap', 'VectorMap', 'RasterMap',
    'open_ecosystem_map', 'list_engines',
    '__version__'
]


def __getattr__(name):
    """Lazy import for ecosystem_map and backends modules."""
    if name in ('EcosystemMap', 'VectorMap', 'RasterMap'):
        from . import ecosystem_map
        return getattr(ecosystem_map, name)
    if name in ('open_ecosystem_map', 'list_engines'):
        from . import backends
        return getattr(backends, name)
    raise AttributeError(f"module 'iucn_get_data' has no attribute {name!r}")
