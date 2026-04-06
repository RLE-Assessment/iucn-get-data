"""Shapefile backend for vector ecosystem maps."""

from typing import TYPE_CHECKING

from . import EcosystemBackendEntrypoint
from .parquet import VectorMapParquet, _require_geopandas

if TYPE_CHECKING:
    from ..ecosystem_map import EcosystemMap

_SHAPEFILE_EXTENSIONS = ('.shp', '.shp.zip', '.shx', '.dbf', '.gpkg', '.geojson', '.json', '.zip')


class VectorMapShapefile(VectorMapParquet):
    """Vector ecosystem map loaded from a shapefile or other OGR-supported format.

    Uses geopandas.read_file() instead of read_parquet().
    Inherits all behavior from VectorMapParquet.
    """

    @property
    def data(self):
        """Lazy-load the GeoDataFrame from the file."""
        if self._data is None:
            gpd = _require_geopandas()
            self._data = gpd.read_file(self.asset_id)
        return self._data

    @data.setter
    def data(self, value):
        self._data = value


class ShapefileBackend(EcosystemBackendEntrypoint):
    """Backend entrypoint for shapefiles and other OGR vector formats."""

    priority = 10

    @classmethod
    def guess_can_open(cls, data) -> bool:
        return (
            isinstance(data, str)
            and data.lower().endswith(_SHAPEFILE_EXTENSIONS)
        )

    @classmethod
    def open_ecosystem_map(cls, data, **kwargs) -> "EcosystemMap":
        return VectorMapShapefile(data, **kwargs)
