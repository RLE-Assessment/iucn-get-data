"""Earth Engine raster backend for ecosystem maps."""

from typing import TYPE_CHECKING

from . import EcosystemBackendEntrypoint
from ._ee_common import _require_ee, _is_file_path, _get_cached_asset_type, _resolve_data
from ..ecosystem_map import RasterMap

if TYPE_CHECKING:
    import pandas as pd


class RasterMapGEE(RasterMap):
    """Raster ecosystem map from Earth Engine (ee.Image).

    Attributes:
        asset_id: The Earth Engine asset ID (None if created from EE object directly).
        asset_type: Always 'IMAGE'.
        data: The ee.Image containing ecosystem data.
        ecosystem_band: Name of the categorical band containing ecosystem IDs.
        ecosystem_dataframe: DataFrame mapping ecosystem IDs to GET codes.
    """

    def __init__(self, data, ecosystem_band: str, ecosystem_dataframe: "pd.DataFrame", **kwargs):
        if hasattr(self, '_resolved'):
            self.asset_id, self.asset_type, self.data = self._resolved
            del self._resolved
        else:
            self.asset_id, self.asset_type, self.data = _resolve_data(data)
        self.ecosystem_band = ecosystem_band
        self.ecosystem_dataframe = ecosystem_dataframe

    def _get_band_names(self) -> list[str]:
        return self.data.bandNames().getInfo()


class EERasterBackend(EcosystemBackendEntrypoint):
    """Backend entrypoint for Earth Engine raster assets."""

    priority = 50

    @classmethod
    def guess_can_open(cls, data) -> bool:
        # Direct EE object check
        try:
            if hasattr(data, 'name') and callable(data.name) and data.name() == 'Image':
                return True
        except Exception:
            pass

        # String asset ID check
        if isinstance(data, str) and not _is_file_path(data):
            asset_type = _get_cached_asset_type(data)
            return asset_type == 'IMAGE'

        return False

    @classmethod
    def open_ecosystem_map(cls, data, **kwargs):
        return RasterMapGEE(data, **kwargs)
