"""IUCN Get Data - Tools for working with IUCN Global Ecosystem Typology data."""

from importlib.metadata import version

from .main import (
    get_realms, get_biomes, get_groups,
    Typology, Realm, Biome, FunctionalGroup
)

__version__ = version("iucn-get-data")
__all__ = [
    'get_realms', 'get_biomes', 'get_groups',
    'Typology', 'Realm', 'Biome', 'FunctionalGroup',
    '__version__'
]
