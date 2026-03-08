"""Shared helpers for Earth Engine backends."""

import functools


def _require_ee():
    """Import and return the ee module, raising a clear error if not installed."""
    try:
        import ee
        return ee
    except ImportError:
        raise ImportError(
            "earthengine-api is required for Earth Engine backends. "
            "Install it with: pip install iucn-get-data[ee]"
        ) from None


def _is_file_path(data) -> bool:
    """Check if data is a file path (local or gs://) rather than an EE asset ID."""
    if not isinstance(data, str):
        return False
    if data.startswith('gs://'):
        return True
    for ext in ('.parquet', '.tif', '.tiff'):
        if data.endswith(ext) or data.lower().endswith(ext):
            return True
    return False


@functools.lru_cache(maxsize=64)
def _get_cached_asset_type(asset_id: str) -> str | None:
    """Look up an EE asset type, caching to avoid duplicate API calls.

    Returns the asset type string ('TABLE', 'IMAGE', etc.) or None on error.
    """
    try:
        ee = _require_ee()
        asset_info = ee.data.getAsset(asset_id)
        return asset_info['type']
    except Exception:
        return None


def _resolve_data(data):
    """Resolve data argument to (asset_id, asset_type, ee_data).

    Args:
        data: Earth Engine asset ID string, ee.FeatureCollection, or ee.Image.

    Returns:
        Tuple of (asset_id, asset_type, ee_data).

    Raises:
        ValueError: If the data type is not supported.
    """
    ee = _require_ee()

    if isinstance(data, str):
        asset_info = ee.data.getAsset(data)
        asset_type = asset_info['type']
        if asset_type == 'TABLE':
            return data, asset_type, ee.FeatureCollection(data)
        elif asset_type == 'IMAGE':
            return data, asset_type, ee.Image(data)
        else:
            raise ValueError(
                f"Unsupported asset type '{asset_type}' for asset '{data}'. "
                "Expected 'TABLE' (FeatureCollection) or 'IMAGE'."
            )
    else:
        type_name = data.name()
        if type_name == 'FeatureCollection':
            return None, 'TABLE', data
        elif type_name == 'Image':
            return None, 'IMAGE', data
        else:
            raise ValueError(
                f"Unsupported data type '{type_name}'. "
                "Expected ee.FeatureCollection or ee.Image."
            )
