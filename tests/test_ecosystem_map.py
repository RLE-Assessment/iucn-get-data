"""Tests for ecosystem map classes and open_ecosystem_map."""

import json
from pathlib import Path

import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock

from iucn_get_data.backends import open_ecosystem_map
from iucn_get_data.backends._ee_common import _resolve_data, _is_file_path
from iucn_get_data.backends.parquet import VectorMapParquet
from iucn_get_data.backends.cog import RasterMapCog
from iucn_get_data.backends.ee_vector import VectorMapGEE
from iucn_get_data.backends.ee_raster import RasterMapGEE
from iucn_get_data.ecosystem_map import EcosystemMap, VectorMap, RasterMap


# Test DataFrame for raster ecosystem tests
TEST_ECOSYSTEM_DF = pd.DataFrame(
    {'get_level3': ['TF1.2', 'T1.1'], 'get_level456': ['Mangroves', 'Lowland Forest']},
    index=pd.Index([37, 52], name='ecosystem_id')
)


# Test geometry coordinates - region in Asia
TEST_GEOMETRY_COORDS = [[[96.90049099947396, 28.66344485978154],
                          [96.63681912447396, 28.185183529731013],
                          [97.71347928072396, 27.46620702497436],
                          [98.94340660274452, 27.72538824708764],
                          [97.93320584322396, 28.528398342301788],
                          [97.38422117062748, 28.654760045064048]]]


@pytest.mark.unit
class TestIsFilePath:
    """Tests for the _is_file_path helper."""

    def test_gs_uri(self):
        assert _is_file_path('gs://bucket/path/eco.parquet') is True

    def test_local_parquet(self):
        assert _is_file_path('/data/eco.parquet') is True

    def test_local_tif(self):
        assert _is_file_path('/data/eco.tif') is True

    def test_local_tiff(self):
        assert _is_file_path('/data/eco.tiff') is True

    def test_ee_asset_id(self):
        assert _is_file_path('projects/my-proj/assets/vector') is False

    def test_non_string(self):
        assert _is_file_path(42) is False


@pytest.mark.unit
class TestClassHierarchy:
    """Tests for the EcosystemMap -> VectorMap/RasterMap class hierarchy."""

    def test_vector_map_parquet_is_vector_map(self):
        eco = VectorMapParquet('/data/eco.parquet', get_level3_column='EFG1')
        assert isinstance(eco, VectorMap)
        assert isinstance(eco, EcosystemMap)

    def test_raster_map_cog_is_raster_map(self):
        eco = RasterMapCog('/data/eco.tif', ecosystem_band='b1', ecosystem_dataframe=TEST_ECOSYSTEM_DF)
        assert isinstance(eco, RasterMap)
        assert isinstance(eco, EcosystemMap)

    def test_vector_map_gee_is_vector_map(self):
        mock_fc = Mock()
        mock_fc.name.return_value = 'FeatureCollection'
        with patch('iucn_get_data.backends._ee_common._require_ee'):
            eco = VectorMapGEE(mock_fc, get_level3_column='EFG1', get_level456_column='COD')
        assert isinstance(eco, VectorMap)
        assert isinstance(eco, EcosystemMap)

    def test_raster_map_gee_is_raster_map(self):
        mock_image = Mock()
        mock_image.name.return_value = 'Image'
        with patch('iucn_get_data.backends._ee_common._require_ee'):
            eco = RasterMapGEE(mock_image, ecosystem_band='b1', ecosystem_dataframe=TEST_ECOSYSTEM_DF)
        assert isinstance(eco, RasterMap)
        assert isinstance(eco, EcosystemMap)


@pytest.mark.unit
class TestVectorMapGEE:
    """Tests for the VectorMapGEE class."""

    @patch('iucn_get_data.backends._ee_common._require_ee')
    def test_loads_vector_asset(self, mock_require_ee):
        mock_ee = MagicMock()
        mock_require_ee.return_value = mock_ee
        mock_ee.data.getAsset.return_value = {'type': 'TABLE'}
        mock_fc_instance = Mock()
        mock_ee.FeatureCollection.return_value = mock_fc_instance

        eco = VectorMapGEE(
            data='projects/test/assets/vector_asset',
            get_level3_column='EFG1',
            get_level456_column='COD'
        )

        mock_ee.data.getAsset.assert_called_once_with('projects/test/assets/vector_asset')
        mock_ee.FeatureCollection.assert_called_once_with('projects/test/assets/vector_asset')
        assert eco.asset_type == 'TABLE'
        assert eco.data == mock_fc_instance

    @patch('iucn_get_data.backends._ee_common._require_ee')
    def test_stores_asset_id(self, mock_require_ee):
        mock_ee = MagicMock()
        mock_require_ee.return_value = mock_ee
        mock_ee.data.getAsset.return_value = {'type': 'TABLE'}

        asset_id = 'projects/goog-rle-assessments/assets/columbia/GETCol'
        eco = VectorMapGEE(asset_id, get_level3_column='EFG1', get_level456_column='COD')
        assert eco.asset_id == asset_id

    def test_accepts_featurecollection(self):
        mock_fc = Mock()
        mock_fc.name.return_value = 'FeatureCollection'
        with patch('iucn_get_data.backends._ee_common._require_ee'):
            eco = VectorMapGEE(mock_fc, get_level3_column='EFG1', get_level456_column='COD')
        assert eco.asset_type == 'TABLE'
        assert eco.data == mock_fc
        assert eco.asset_id is None

    @patch('iucn_get_data.backends.ee_vector._require_ee')
    @patch('iucn_get_data.backends._ee_common._require_ee')
    def test_functional_group_dataframe(self, mock_common_ee, mock_vector_ee):
        mock_ee = MagicMock()
        mock_common_ee.return_value = mock_ee
        mock_vector_ee.return_value = mock_ee
        mock_ee.data.getAsset.return_value = {'type': 'TABLE'}

        mock_fc_instance = Mock()
        mock_ee.FeatureCollection.return_value = mock_fc_instance

        mock_first = Mock()
        mock_property_names = Mock()
        mock_fc_instance.first.return_value = mock_first
        mock_first.propertyNames.return_value = mock_property_names
        mock_property_names.remove.return_value = mock_property_names

        mock_distinct_fc = Mock()
        mock_fc_instance.distinct.return_value = mock_distinct_fc

        mock_size = Mock()
        mock_distinct_fc.size.return_value = mock_size
        mock_list = Mock()
        mock_distinct_fc.toList.return_value = mock_list

        records = [
            {'COD': 'B36', 'ECO_NAME': 'Test Ecosystem', 'EFG1': 'MFT1.2'},
            {'COD': 'B10', 'ECO_NAME': 'Another Ecosystem', 'EFG1': 'T1.2'}
        ]
        mock_mapped_list = Mock()
        mock_list.map.return_value = mock_mapped_list
        mock_mapped_list.getInfo.return_value = records

        mock_ee.Feature.return_value = Mock()

        eco = VectorMapGEE(
            'projects/test/assets/vector_asset',
            get_level3_column='EFG1',
            get_level456_column='COD'
        )
        df = eco.functional_group_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert isinstance(df.index, pd.MultiIndex)
        assert df.index.names == ['EFG1', 'COD']
        assert ('MFT1.2', 'B36') in df.index
        assert ('T1.2', 'B10') in df.index
        assert 'EFG1' not in df.columns
        assert 'COD' not in df.columns


@pytest.mark.unit
class TestRasterMapGEE:
    """Tests for the RasterMapGEE class."""

    @patch('iucn_get_data.backends._ee_common._require_ee')
    def test_loads_raster_asset(self, mock_require_ee):
        mock_ee = MagicMock()
        mock_require_ee.return_value = mock_ee
        mock_ee.data.getAsset.return_value = {'type': 'IMAGE'}
        mock_image_instance = Mock()
        mock_ee.Image.return_value = mock_image_instance

        eco = RasterMapGEE(
            'projects/test/assets/raster_asset',
            ecosystem_band='b1',
            ecosystem_dataframe=TEST_ECOSYSTEM_DF,
        )

        mock_ee.data.getAsset.assert_called_once_with('projects/test/assets/raster_asset')
        mock_ee.Image.assert_called_once_with('projects/test/assets/raster_asset')
        assert eco.asset_type == 'IMAGE'
        assert eco.data == mock_image_instance

    def test_accepts_image(self):
        mock_image = Mock()
        mock_image.name.return_value = 'Image'
        with patch('iucn_get_data.backends._ee_common._require_ee'):
            eco = RasterMapGEE(
                mock_image,
                ecosystem_band='b1',
                ecosystem_dataframe=TEST_ECOSYSTEM_DF,
            )
        assert eco.asset_type == 'IMAGE'
        assert eco.data == mock_image
        assert eco.asset_id is None

    @patch('iucn_get_data.backends._ee_common._require_ee')
    def test_functional_group_dataframe(self, mock_require_ee):
        mock_ee = MagicMock()
        mock_require_ee.return_value = mock_ee
        mock_ee.data.getAsset.return_value = {'type': 'IMAGE'}

        eco = RasterMapGEE(
            'projects/test/assets/raster',
            ecosystem_band='b1',
            ecosystem_dataframe=TEST_ECOSYSTEM_DF,
        )
        result = eco.functional_group_dataframe()
        pd.testing.assert_frame_equal(result, TEST_ECOSYSTEM_DF)

    def test_direct_instantiation(self):
        mock_image = Mock()
        mock_image.name.return_value = 'Image'
        with patch('iucn_get_data.backends._ee_common._require_ee'):
            eco = RasterMapGEE(
                mock_image,
                ecosystem_band='classification',
                ecosystem_dataframe=TEST_ECOSYSTEM_DF,
            )
        assert eco.asset_type == 'IMAGE'
        assert eco.ecosystem_band == 'classification'


@pytest.mark.unit
class TestVectorMapParquet:
    """Tests for the VectorMapParquet class."""

    def test_direct_instantiation(self):
        eco = VectorMapParquet(
            '/data/eco.parquet',
            get_level3_column='EFG1',
            get_level456_column='COD'
        )
        assert eco.asset_id == '/data/eco.parquet'
        assert eco.asset_type == 'TABLE'
        assert eco.get_level3_column == 'EFG1'
        assert eco.get_level456_column == 'COD'

    @patch('iucn_get_data.backends.parquet._require_geopandas')
    def test_lazy_data_loading(self, mock_require_gpd):
        mock_gpd = MagicMock()
        mock_require_gpd.return_value = mock_gpd
        mock_gdf = MagicMock()
        mock_gpd.read_parquet.return_value = mock_gdf

        eco = VectorMapParquet('/data/eco.parquet')

        mock_gpd.read_parquet.assert_not_called()
        result = eco.data
        mock_gpd.read_parquet.assert_called_once_with('/data/eco.parquet')
        assert result == mock_gdf

    @patch('iucn_get_data.backends.parquet._require_geopandas')
    def test_functional_group_dataframe(self, mock_require_gpd):
        mock_gpd = MagicMock()
        mock_require_gpd.return_value = mock_gpd

        import geopandas as gpd
        from shapely.geometry import Point

        gdf = gpd.GeoDataFrame({
            'EFG1': ['MFT1.2', 'T1.2', 'T1.2'],
            'COD': ['B36', 'B10', 'B10'],
            'ECO_NAME': ['Mangroves', 'Dry Forest', 'Dry Forest'],
            'OBJECTID': [1, 2, 3],
            'geometry': [Point(0, 0), Point(1, 1), Point(2, 2)],
        })
        mock_gpd.read_parquet.return_value = gdf

        eco = VectorMapParquet(
            '/data/eco.parquet',
            get_level3_column='EFG1',
            get_level456_column='COD'
        )
        df = eco.functional_group_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert isinstance(df.index, pd.MultiIndex)
        assert len(df) == 2
        assert 'geometry' not in df.columns
        assert 'OBJECTID' not in df.columns
        assert ('MFT1.2', 'B36') in df.index
        assert ('T1.2', 'B10') in df.index

    def test_functional_group_dataframe_raises_without_columns(self):
        eco = VectorMapParquet('/data/eco.parquet')
        with pytest.raises(ValueError, match="Both get_level3_column and get_level456_column"):
            eco.functional_group_dataframe()


@pytest.mark.unit
class TestRasterMapCog:
    """Tests for the RasterMapCog class."""

    def test_direct_instantiation(self):
        eco = RasterMapCog(
            '/data/eco.tif',
            ecosystem_band='classification',
            ecosystem_dataframe=TEST_ECOSYSTEM_DF,
        )
        assert eco.asset_id == '/data/eco.tif'
        assert eco.asset_type == 'IMAGE'
        assert eco.ecosystem_band == 'classification'
        pd.testing.assert_frame_equal(eco.ecosystem_dataframe, TEST_ECOSYSTEM_DF)

    @patch('iucn_get_data.backends.cog._require_rioxarray')
    @patch('xarray.open_dataset')
    def test_lazy_data_loading(self, mock_open_dataset, mock_require_rio):
        mock_ds = MagicMock()
        mock_open_dataset.return_value = mock_ds

        eco = RasterMapCog(
            '/data/eco.tif',
            ecosystem_band='b1',
            ecosystem_dataframe=TEST_ECOSYSTEM_DF,
        )

        mock_open_dataset.assert_not_called()
        result = eco.data
        mock_open_dataset.assert_called_once_with('/data/eco.tif', engine='rasterio')
        assert result == mock_ds

    def test_functional_group_dataframe_returns_provided_df(self):
        eco = RasterMapCog(
            '/data/eco.tif',
            ecosystem_band='b1',
            ecosystem_dataframe=TEST_ECOSYSTEM_DF,
        )
        result = eco.functional_group_dataframe()
        pd.testing.assert_frame_equal(result, TEST_ECOSYSTEM_DF)


@pytest.mark.unit
class TestOpenEcosystemMap:
    """Tests for the open_ecosystem_map function."""

    def test_routes_parquet_path(self):
        eco = open_ecosystem_map(
            '/data/eco.parquet',
            get_level3_column='EFG1',
            get_level456_column='COD'
        )
        assert isinstance(eco, VectorMapParquet)
        assert eco.asset_id == '/data/eco.parquet'
        assert eco.asset_type == 'TABLE'
        assert eco.get_level3_column == 'EFG1'

    def test_routes_gs_parquet(self):
        eco = open_ecosystem_map(
            'gs://bucket/eco.parquet',
            get_level3_column='EFG1',
            get_level456_column='COD'
        )
        assert isinstance(eco, VectorMapParquet)

    def test_routes_tif_path(self):
        eco = open_ecosystem_map(
            '/data/eco.tif',
            ecosystem_band='b1',
            ecosystem_dataframe=TEST_ECOSYSTEM_DF,
        )
        assert isinstance(eco, RasterMapCog)
        assert eco.asset_id == '/data/eco.tif'
        assert eco.asset_type == 'IMAGE'
        assert eco.ecosystem_band == 'b1'

    def test_routes_gs_tif(self):
        eco = open_ecosystem_map(
            'gs://bucket/eco.tif',
            ecosystem_band='b1',
            ecosystem_dataframe=TEST_ECOSYSTEM_DF,
        )
        assert isinstance(eco, RasterMapCog)

    def test_explicit_engine_parquet(self):
        eco = open_ecosystem_map(
            '/data/eco.parquet',
            engine='parquet',
            get_level3_column='EFG1',
        )
        assert isinstance(eco, VectorMapParquet)

    def test_unknown_engine_raises(self):
        with pytest.raises(ValueError, match="Unknown engine"):
            open_ecosystem_map('/data/eco.parquet', engine='nonexistent')

    def test_no_matching_backend_raises(self):
        with pytest.raises(ValueError, match="No backend can handle"):
            open_ecosystem_map(12345)


@pytest.mark.unit
class TestResolveData:
    """Tests for _resolve_data."""

    @patch('iucn_get_data.backends._ee_common._require_ee')
    def test_raises_for_unsupported_asset_type(self, mock_require_ee):
        mock_ee = MagicMock()
        mock_require_ee.return_value = mock_ee
        mock_ee.data.getAsset.return_value = {'type': 'FOLDER'}

        with pytest.raises(ValueError, match="Unsupported asset type 'FOLDER'"):
            _resolve_data('projects/test/assets/folder')

    def test_raises_for_invalid_ee_type(self):
        mock_geometry = Mock()
        mock_geometry.name.return_value = 'Geometry'

        with patch('iucn_get_data.backends._ee_common._require_ee'):
            with pytest.raises(ValueError, match="Unsupported data type 'Geometry'"):
                _resolve_data(mock_geometry)


def get_test_geometry():
    """Get test geometry (only call after ee.Initialize())."""
    import ee
    return ee.Geometry.Polygon(TEST_GEOMETRY_COORDS)


@pytest.mark.integration
class TestIntegrationWithRealEE:
    """Integration tests using real Earth Engine objects (requires authentication)."""

    @pytest.fixture(autouse=True)
    def setup_ee(self):
        """Initialize Earth Engine before each test."""
        try:
            import ee
            from google.auth import default
            credentials, _ = default(scopes=[
                'https://www.googleapis.com/auth/earthengine',
                'https://www.googleapis.com/auth/cloud-platform'
            ])
            ee.Initialize(credentials=credentials, project='goog-rle-assessments')
        except Exception:
            pytest.skip("Earth Engine not authenticated - skipping integration tests")

    def test_vector_integration(self):
        import ee

        test_data_path = Path(__file__).parent / 'test_data' / 'table.json'
        with open(test_data_path) as f:
            table_data = json.load(f)

        fc = ee.FeatureCollection(table_data)
        eco = VectorMapGEE(fc, get_level3_column='EFG1', get_level456_column='Glob_Typol')

        assert eco.asset_id is None
        assert eco.asset_type == 'TABLE'
        assert isinstance(eco.data, ee.FeatureCollection)

        count = eco.data.size().getInfo()
        assert count == 3, f"Expected 3 features, got {count}"

    def test_raster_integration(self):
        import ee

        asset_id = 'projects/goog-rle-assessments/assets/mm_ecosys_v7b'
        test_df = pd.DataFrame(
            {'get_level3': ['TF1.2'], 'get_level456': ['Mangroves']},
            index=pd.Index([37], name='ecosystem_id')
        )

        eco = RasterMapGEE(
            asset_id,
            ecosystem_band='b1',
            ecosystem_dataframe=test_df,
        )

        assert eco.asset_id == asset_id
        assert eco.asset_type == 'IMAGE'
        assert isinstance(eco.data, ee.Image)
        assert eco.ecosystem_band == 'b1'

        band_names = eco.data.bandNames().getInfo()
        assert len(band_names) > 0

    def test_functional_group_dataframe_integration(self):
        import ee

        test_data_path = Path(__file__).parent / 'test_data' / 'table.json'
        with open(test_data_path) as f:
            table_data = json.load(f)

        fc = ee.FeatureCollection(table_data)
        eco = VectorMapGEE(fc, get_level3_column='EFG1', get_level456_column='Glob_Typol')
        df = eco.functional_group_dataframe()

        assert isinstance(df, pd.DataFrame)

        excluded_cols = {'OBJECTID', 'Shape_Area', 'Shape_Leng', 'system:index'}
        for col in excluded_cols:
            assert col not in df.columns

        assert len(df) > 0

    def test_open_ecosystem_map_with_ee_asset(self):
        """Integration test for open_ecosystem_map with an EE asset."""
        import ee

        asset_id = 'projects/goog-rle-assessments/assets/mm_ecosys_v7b'
        test_df = pd.DataFrame(
            {'get_level3': ['TF1.2'], 'get_level456': ['Mangroves']},
            index=pd.Index([37], name='ecosystem_id')
        )

        eco = open_ecosystem_map(
            asset_id,
            ecosystem_band='b1',
            ecosystem_dataframe=test_df,
        )

        assert isinstance(eco, RasterMapGEE)
        assert isinstance(eco, RasterMap)
        assert eco.asset_id == asset_id

    def test_featurecollection_from_local_test_data(self):
        import ee

        test_data_path = Path(__file__).parent / 'test_data' / 'table.json'
        with open(test_data_path) as f:
            table_data = json.load(f)

        fc = ee.FeatureCollection(table_data)

        assert fc.size().getInfo() == 3

        first_feature = fc.first().getInfo()
        assert 'EFG1' in first_feature['properties']
        assert 'Glob_Typol' in first_feature['properties']

        efg1_values = fc.aggregate_array('EFG1').getInfo()
        assert 'MFT1.2' in efg1_values
        assert 'T1.2' in efg1_values
