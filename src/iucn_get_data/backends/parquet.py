"""GeoParquet backend for vector ecosystem maps."""

from typing import TYPE_CHECKING

from . import EcosystemBackendEntrypoint
from ._ee_common import _is_file_path
from ..ecosystem_map import VectorMap

if TYPE_CHECKING:
    import pandas as pd


def _require_geopandas():
    """Import and return geopandas, raising a clear error if not installed."""
    try:
        import geopandas as gpd
        return gpd
    except ImportError:
        raise ImportError(
            "geopandas is required for Parquet ecosystem maps. "
            "Install it with: pip install iucn-get-data[gcs]"
        ) from None


class VectorMapParquet(VectorMap):
    """Vector ecosystem map stored as a GeoParquet file.

    Supports local paths and gs:// URIs (requires gcsfs for GCS access).

    Attributes:
        asset_id: The file path (local or gs://).
        asset_type: Always 'TABLE'.
        get_level3_column: Column name for GET Level 3 ecosystem functional group codes.
        get_level456_column: Column name for GET Level 4 ecosystem type codes.
        data: The GeoDataFrame (lazy-loaded on first access).
    """

    def __init__(self, data, get_level3_column=None, get_level456_column=None, **kwargs):
        self.asset_id = data
        self.asset_type = 'TABLE'
        self.get_level3_column = get_level3_column
        self.get_level456_column = get_level456_column
        self.cmap = kwargs.get('cmap')
        self._data = None

    @property
    def data(self):
        """Lazy-load the GeoDataFrame from the Parquet file."""
        if self._data is None:
            gpd = _require_geopandas()
            self._data = gpd.read_parquet(self.asset_id)
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

    def _get_feature_count(self) -> int:
        return len(self.data)

    def _get_preview_rows(self, n: int = 5) -> tuple[list[str], list[dict]]:
        preview = self.data.head(n).drop(columns='geometry', errors='ignore')
        props = list(preview.columns)
        rows = [dict(row) for _, row in preview.iterrows()]
        return props, rows

    def functional_group_dataframe(self) -> "pd.DataFrame":
        """Return functional groups as a pandas DataFrame with MultiIndex.

        Reads the Parquet file, drops geometry, and returns distinct
        combinations of GET Level 3 and Level 4 columns as a MultiIndex.
        """
        import pandas as pd

        if self.get_level3_column is None or self.get_level456_column is None:
            raise ValueError(
                "Both get_level3_column and get_level456_column must be specified "
                "to use functional_group_dataframe()"
            )

        exclude_cols = ['OBJECTID', 'Shape_Area', 'Shape_Leng', 'system:index', 'geometry']
        df = pd.DataFrame(self.data.drop(columns='geometry', errors='ignore'))
        df = df.drop(columns=[c for c in exclude_cols if c in df.columns])

        df = df.drop_duplicates(subset=[self.get_level3_column, self.get_level456_column])
        return df.set_index([self.get_level3_column, self.get_level456_column])


class ParquetBackend(EcosystemBackendEntrypoint):
    """Backend entrypoint for GeoParquet files."""

    priority = 10

    @classmethod
    def guess_can_open(cls, data) -> bool:
        return isinstance(data, str) and _is_file_path(data) and data.endswith('.parquet')

    @classmethod
    def open_ecosystem_map(cls, data, **kwargs):
        return VectorMapParquet(data, **kwargs)
