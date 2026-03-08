"""Tests for backend plugin discovery and registration."""

import pytest
from unittest.mock import patch

from iucn_get_data.backends import (
    EcosystemBackendEntrypoint,
    list_engines,
    open_ecosystem_map,
    refresh_engines,
)
from iucn_get_data.backends.parquet import ParquetBackend, VectorMapParquet
from iucn_get_data.backends.cog import CogBackend, RasterMapCog
from iucn_get_data.backends.ee_vector import EEVectorBackend, VectorMapGEE
from iucn_get_data.backends.ee_raster import EERasterBackend, RasterMapGEE


@pytest.fixture(autouse=True)
def clear_engine_cache():
    """Clear the engine cache before and after each test."""
    refresh_engines()
    yield
    refresh_engines()


@pytest.mark.unit
class TestListEngines:
    """Tests for list_engines() discovery."""

    def test_discovers_all_builtin_backends(self):
        engines = list_engines()
        assert 'parquet' in engines
        assert 'cog' in engines
        assert 'ee_vector' in engines
        assert 'ee_raster' in engines

    def test_returns_correct_backend_classes(self):
        engines = list_engines()
        assert engines['parquet'] is ParquetBackend
        assert engines['cog'] is CogBackend
        assert engines['ee_vector'] is EEVectorBackend
        assert engines['ee_raster'] is EERasterBackend

    def test_all_backends_are_entrypoint_subclasses(self):
        engines = list_engines()
        for name, backend in engines.items():
            assert issubclass(backend, EcosystemBackendEntrypoint), (
                f"{name} is not a subclass of EcosystemBackendEntrypoint"
            )

    def test_caches_result(self):
        engines1 = list_engines()
        engines2 = list_engines()
        assert engines1 is engines2

    def test_refresh_clears_cache(self):
        engines1 = list_engines()
        refresh_engines()
        engines2 = list_engines()
        assert engines1 is not engines2
        assert engines1 == engines2


@pytest.mark.unit
class TestBackendPriority:
    """Tests for backend priority ordering."""

    def test_file_backends_have_lower_priority(self):
        assert ParquetBackend.priority < EEVectorBackend.priority
        assert CogBackend.priority < EERasterBackend.priority

    def test_file_backends_priority_is_10(self):
        assert ParquetBackend.priority == 10
        assert CogBackend.priority == 10

    def test_ee_backends_priority_is_50(self):
        assert EEVectorBackend.priority == 50
        assert EERasterBackend.priority == 50


@pytest.mark.unit
class TestGuessCanOpen:
    """Tests for guess_can_open on each backend."""

    def test_parquet_matches_parquet_path(self):
        assert ParquetBackend.guess_can_open('/data/eco.parquet') is True

    def test_parquet_matches_gs_parquet(self):
        assert ParquetBackend.guess_can_open('gs://bucket/eco.parquet') is True

    def test_parquet_rejects_tif(self):
        assert ParquetBackend.guess_can_open('/data/eco.tif') is False

    def test_parquet_rejects_ee_asset(self):
        assert ParquetBackend.guess_can_open('projects/test/assets/foo') is False

    def test_parquet_rejects_non_string(self):
        assert ParquetBackend.guess_can_open(42) is False

    def test_cog_matches_tif_path(self):
        assert CogBackend.guess_can_open('/data/eco.tif') is True

    def test_cog_matches_tiff_path(self):
        assert CogBackend.guess_can_open('/data/eco.tiff') is True

    def test_cog_matches_gs_tif(self):
        assert CogBackend.guess_can_open('gs://bucket/eco.tif') is True

    def test_cog_rejects_parquet(self):
        assert CogBackend.guess_can_open('/data/eco.parquet') is False

    def test_cog_rejects_non_string(self):
        assert CogBackend.guess_can_open(42) is False

    def test_ee_vector_rejects_file_path(self):
        assert EEVectorBackend.guess_can_open('/data/eco.parquet') is False

    def test_ee_raster_rejects_file_path(self):
        assert EERasterBackend.guess_can_open('/data/eco.tif') is False

    def test_ee_vector_rejects_non_string_non_ee(self):
        assert EEVectorBackend.guess_can_open(42) is False

    def test_ee_raster_rejects_non_string_non_ee(self):
        assert EERasterBackend.guess_can_open(42) is False


@pytest.mark.unit
class TestMockThirdPartyBackend:
    """Test that a third-party backend could be registered."""

    def test_custom_backend_can_be_created(self):
        from iucn_get_data.ecosystem_map import EcosystemMap

        class MyBackend(EcosystemBackendEntrypoint):
            priority = 5

            @classmethod
            def guess_can_open(cls, data):
                return isinstance(data, str) and data.endswith('.custom')

            @classmethod
            def open_ecosystem_map(cls, data, **kwargs):
                return None  # would return a real instance

        assert MyBackend.guess_can_open('test.custom') is True
        assert MyBackend.guess_can_open('test.parquet') is False
        assert MyBackend.priority == 5
