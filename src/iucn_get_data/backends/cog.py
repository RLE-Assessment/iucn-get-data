"""COG (Cloud Optimized GeoTIFF) backend for raster ecosystem maps."""

from typing import TYPE_CHECKING

from . import EcosystemBackendEntrypoint
from ._ee_common import _is_file_path
from ..ecosystem_map import RasterMap

if TYPE_CHECKING:
    import pandas as pd


def _require_rioxarray():
    """Import and return rioxarray, raising a clear error if not installed."""
    try:
        import rioxarray
        return rioxarray
    except ImportError:
        raise ImportError(
            "rioxarray is required for COG ecosystem maps. "
            "Install it with: pip install iucn-get-data[cog]"
        ) from None


class RasterMapCog(RasterMap):
    """Raster ecosystem map stored as a Cloud Optimized GeoTIFF (COG).

    Supports local paths and gs:// URIs.

    Attributes:
        asset_id: The file path (local or gs://).
        asset_type: Always 'IMAGE'.
        ecosystem_band: Name of the band containing ecosystem IDs.
        ecosystem_dataframe: DataFrame mapping ecosystem IDs to GET codes.
        data: The rioxarray DataArray (lazy-loaded on first access).
    """

    def __init__(self, data, ecosystem_band: str, ecosystem_dataframe: "pd.DataFrame", **kwargs):
        self.asset_id = data
        self.asset_type = 'IMAGE'
        self.ecosystem_band = ecosystem_band
        self.ecosystem_dataframe = ecosystem_dataframe
        self._data = None

    @property
    def data(self):
        """Lazy-load the DataArray from the COG file."""
        if self._data is None:
            _require_rioxarray()
            import xarray as xr
            self._data = xr.open_dataset(self.asset_id, engine="rasterio")
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

    def _get_band_names(self) -> list[str]:
        return list(self.data.data_vars)


class CogBackend(EcosystemBackendEntrypoint):
    """Backend entrypoint for Cloud Optimized GeoTIFF files."""

    priority = 10

    @classmethod
    def guess_can_open(cls, data) -> bool:
        if not isinstance(data, str):
            return False
        lower = data.lower()
        return _is_file_path(data) and (lower.endswith('.tif') or lower.endswith('.tiff'))

    @classmethod
    def open_ecosystem_map(cls, data, **kwargs):
        return RasterMapCog(data, **kwargs)
