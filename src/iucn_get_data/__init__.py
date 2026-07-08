"""IUCN Get Data - Tools for working with IUCN Global Ecosystem Typology data."""

from importlib.metadata import version

from .core import (
    get_realms, get_biomes, get_groups,
    Typology, Realm, Biome, FunctionalGroup
)
from .vocabulary import load_vocabulary, build_realms_from_graph

__version__ = version("iucn-get-data")
__all__ = [
    'get_realms', 'get_biomes', 'get_groups',
    'Typology', 'Realm', 'Biome', 'FunctionalGroup',
    'load_vocabulary', 'build_realms_from_graph',
    '__version__'
]
