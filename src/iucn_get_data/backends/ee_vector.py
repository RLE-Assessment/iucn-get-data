"""Earth Engine vector backend for ecosystem maps."""

from typing import TYPE_CHECKING

from . import EcosystemBackendEntrypoint
from ._ee_common import _require_ee, _is_file_path, _get_cached_asset_type, _resolve_data
from ..ecosystem_map import VectorMap

if TYPE_CHECKING:
    import pandas as pd


class VectorMapGEE(VectorMap):
    """Vector ecosystem map from Earth Engine (ee.FeatureCollection).

    Attributes:
        asset_id: The Earth Engine asset ID (None if created from EE object directly).
        asset_type: Always 'TABLE'.
        data: The ee.FeatureCollection containing ecosystem data.
        get_level3_column: Column name for GET Level 3 ecosystem functional group codes.
        get_level456_column: Column name for GET Level 4 ecosystem type codes.
    """

    def __init__(self, data, get_level3_column=None, get_level456_column=None, **kwargs):
        if hasattr(self, '_resolved'):
            self.asset_id, self.asset_type, self.data = self._resolved
            del self._resolved
        else:
            self.asset_id, self.asset_type, self.data = _resolve_data(data)
        self.get_level3_column = get_level3_column
        self.get_level456_column = get_level456_column
        self.cmap = kwargs.get('cmap')

    def _get_feature_count(self) -> int:
        return self.data.size().getInfo()

    def _get_preview_rows(self, n: int = 5) -> tuple[list[str], list[dict]]:
        head_features = self.data.limit(n).getInfo()['features']
        if not head_features:
            return [], []
        props = list(head_features[0].get('properties', {}).keys())
        rows = [f.get('properties', {}) for f in head_features]
        return props, rows

    def functional_group_dataframe(self) -> "pd.DataFrame":
        """Return functional groups as a pandas DataFrame with MultiIndex.

        Uses Earth Engine server-side grouped reduction for efficiency.
        """
        import pandas as pd
        ee = _require_ee()

        if self.get_level3_column is None or self.get_level456_column is None:
            raise ValueError(
                "Both get_level3_column and get_level456_column must be specified "
                "to use the dataframe property"
            )

        exclude_cols = ['OBJECTID', 'Shape_Area', 'Shape_Leng', 'system:index']

        group_cols = self.data.first().propertyNames()
        for col in exclude_cols:
            group_cols = group_cols.remove(col)

        distinct_pairs_fc = self.data.distinct([self.get_level3_column, self.get_level456_column])

        def extract_columns(feature):
            return ee.Feature(feature).toDictionary(group_cols)

        distinct_pairs_list = distinct_pairs_fc.toList(distinct_pairs_fc.size()).map(extract_columns)

        records = distinct_pairs_list.getInfo()
        df = pd.DataFrame(records)
        return df.set_index([self.get_level3_column, self.get_level456_column])


class EEVectorBackend(EcosystemBackendEntrypoint):
    """Backend entrypoint for Earth Engine vector assets."""

    priority = 50

    @classmethod
    def guess_can_open(cls, data) -> bool:
        # Direct EE object check
        try:
            if hasattr(data, 'name') and callable(data.name) and data.name() == 'FeatureCollection':
                return True
        except Exception:
            pass

        # String asset ID check
        if isinstance(data, str) and not _is_file_path(data):
            asset_type = _get_cached_asset_type(data)
            return asset_type == 'TABLE'

        return False

    @classmethod
    def open_ecosystem_map(cls, data, **kwargs):
        return VectorMapGEE(data, **kwargs)
