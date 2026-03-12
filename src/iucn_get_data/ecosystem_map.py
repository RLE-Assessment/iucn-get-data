"""
Base and intermediate classes for ecosystem map datasets.

This module defines the class hierarchy for ecosystem maps mapped to
IUCN Global Ecosystem Typology (GET) functional groups:

- EcosystemMap: base class with shared Jupyter display
- VectorMap: intermediate for vector backends (GET column attributes, HTML preview)
- RasterMap: intermediate for raster backends (band/dataframe attributes, HTML preview)

Concrete backend classes live in iucn_get_data.backends.
"""

import re
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import TYPE_CHECKING

import yaml
from importlib import resources

if TYPE_CHECKING:
    import pandas as pd


@lru_cache(maxsize=1)
def _load_map_style() -> dict:
    """Load and cache the default map style colors from map_style.yaml."""
    style_file = resources.files('iucn_get_data') / 'data' / 'map_style.yaml'
    return yaml.safe_load(style_file.read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def _load_language_data() -> dict:
    """Load and cache the English language data from english.yaml."""
    lang_file = resources.files('iucn_get_data') / 'data' / 'english.yaml'
    return yaml.safe_load(lang_file.read_text(encoding='utf-8'))


@lru_cache(maxsize=1)
def _build_code_name_lookup() -> dict[str, str]:
    """Build a flat {code: name} lookup from the nested language YAML."""
    data = _load_language_data()
    lookup = {}
    for realm in data.get('realms', []):
        lookup[realm['code']] = realm['name']
        for biome in realm.get('biomes', []):
            lookup[biome['code']] = biome['name']
            for fg in biome.get('functional_groups', []):
                lookup[fg['code']] = fg['name']
    return lookup


_STYLE_KEY_TITLES = {
    'realms': 'Realm',
    'biomes': 'Biome',
    'functional_groups': 'Functional Group',
}


def _build_legend_widget(style_key, codes):
    """Build an ipywidgets.HTML legend for the given style key and codes.

    Args:
        style_key: Key in map_style.yaml ('realms', 'biomes', or 'functional_groups').
        codes: Iterable of category codes to include in the legend.

    Returns:
        An ipywidgets.HTML widget with colored swatches and labels.
    """
    from ipywidgets import HTML, Layout

    title = _STYLE_KEY_TITLES.get(style_key, style_key)
    style = _load_map_style().get(style_key, {})
    names = _build_code_name_lookup()
    items = []
    for code in sorted(codes):
        rgb = style.get(code, [128, 128, 128])
        name = names.get(code, code)
        color = f'rgb({rgb[0]},{rgb[1]},{rgb[2]})'
        items.append(
            f'<div style="display:flex;align-items:flex-start;margin:1px 0;'
            f'line-height:1.2">'
            f'<span style="display:inline-block;width:14px;height:14px;'
            f'background:{color};border:1px solid #999;margin-right:6px;'
            f'flex-shrink:0;margin-top:2px"></span>'
            f'<span style="font-size:13px;min-width:50px;flex-shrink:0">{code}</span>'
            f'<span style="font-size:13px;flex:1;min-width:0;'
            f'padding-left:1em;text-indent:-1em">{name}</span></div>'
        )
    header = f'<div style="font-weight:bold;margin-bottom:4px">{title}</div>'
    html = '<div style="padding:8px">' + header + ''.join(items) + '</div>'
    return HTML(html, layout=Layout(
        width='250px', overflow_y='auto', flex='0 0 250px',
    ))


class EcosystemMap(ABC):
    """Base class for all ecosystem map datasets.

    Attributes:
        asset_id: The data source path or asset ID.
        asset_type: The type of data ('TABLE' for vector, 'IMAGE' for raster).
        data: The underlying data object.
    """

    asset_id: str | None
    asset_type: str
    data: object

    def _data_repr_html_(self, meta_rows: list[str]) -> str:
        """Return type-specific HTML content. Subclasses override this."""
        return ""

    def _repr_html_(self) -> str:
        """Return HTML representation for Jupyter notebook display."""
        meta_rows = []
        if self.asset_id:
            meta_rows.append(f"<tr><td><b>Asset ID</b></td><td>{self.asset_id}</td></tr>")
        meta_rows.append(f"<tr><td><b>Asset Type</b></td><td>{self.asset_type}</td></tr>")

        data_table = self._data_repr_html_(meta_rows)

        return f"""
        <table style="border-collapse: collapse;">
            <thead>
                <tr><th colspan="2" style="text-align: left; padding: 8px; background-color: #f0f0f0;">EcosystemMap</th></tr>
            </thead>
            <tbody>
                {''.join(meta_rows)}
            </tbody>
        </table>
        {data_table}
        """

    @abstractmethod
    def functional_group_dataframe(self) -> "pd.DataFrame":
        """Return ecosystem functional groups as a pandas DataFrame."""
        ...


class VectorMap(EcosystemMap):
    """Intermediate base for vector ecosystem map backends.

    Provides shared attributes and HTML rendering for vector data with
    GET Level 3 and Level 4/5/6 column designations.

    Attributes:
        get_level3_column: Column name for GET Level 3 ecosystem functional group codes.
        get_level456_column: Column name for GET Level 4 ecosystem type codes.
    """

    get_level3_column: str | None
    get_level456_column: str | None
    cmap: dict | None

    def get_fill_color(self, alpha=180):
        """Return a per-feature RGBA color array based on get_level456_column values.

        Uses self.cmap if provided, otherwise generates deterministic random colors
        for each unique value in the get_level456_column.

        Args:
            alpha: Alpha transparency (0-255) applied to all colors.

        Returns:
            A numpy uint8 array of shape (n_features, 4).

        Requires lonboard: pip install lonboard
        """
        import hashlib
        from lonboard.colormap import apply_categorical_cmap

        values = self.data[self.get_level456_column]

        if self.cmap is not None:
            cmap = self.cmap
        else:
            unique_vals = values.unique()
            cmap = {}
            for val in unique_vals:
                h = hashlib.md5(str(val).encode()).digest()
                cmap[val] = [h[0], h[1], h[2]]

        return apply_categorical_cmap(values, cmap, alpha=alpha)

    @staticmethod
    def _simplify_geodataframe(gdf, tolerance):
        """Return a GeoDataFrame with simplified geometries, dropping empty results."""
        gdf = gdf.copy()
        gdf['geometry'] = gdf.geometry.simplify(tolerance=tolerance)
        return gdf[~gdf.geometry.is_empty]

    def to_layer(self, alpha=180, stroked=True, get_line_width=2,
                 get_line_color=None, simplify_tolerance=None, **kwargs):
        """Create a lonboard PolygonLayer from this ecosystem map.

        Args:
            alpha: Alpha transparency (0-255) for fill colors.
            stroked: Whether to draw polygon outlines.
            get_line_width: Width of polygon outlines.
            get_line_color: RGBA list for outline color. Defaults to [0, 0, 0, 150].
            simplify_tolerance: Optional geometry simplification tolerance in
                degrees. Reduces vertex count for faster rendering. Try 0.001
                (~111m) for large datasets.
            **kwargs: Additional keyword arguments passed to PolygonLayer.from_geopandas.

        Returns:
            A lonboard PolygonLayer.
        """
        from lonboard import PolygonLayer

        if get_line_color is None:
            get_line_color = [0, 0, 0, 150]

        gdf = self.data
        if simplify_tolerance is not None:
            gdf = self._simplify_geodataframe(gdf, simplify_tolerance)

        # Recompute fill colors against the (possibly filtered) GeoDataFrame
        import hashlib
        from lonboard.colormap import apply_categorical_cmap

        values = gdf[self.get_level456_column]
        if self.cmap is not None:
            cmap = self.cmap
        else:
            unique_vals = values.unique()
            cmap = {}
            for val in unique_vals:
                h = hashlib.md5(str(val).encode()).digest()
                cmap[val] = [h[0], h[1], h[2]]
        fill_color = apply_categorical_cmap(values, cmap, alpha=alpha)

        return PolygonLayer.from_geopandas(
            gdf,
            get_fill_color=fill_color,
            stroked=stroked,
            get_line_width=get_line_width,
            get_line_color=get_line_color,
            **kwargs,
        )

    def to_map(self, alpha=180, stroked=True, get_line_width=2,
               get_line_color=None, simplify_tolerance=None,
               view_state=None, **layer_kwargs):
        """Create a lonboard Map displaying this ecosystem map.

        Args:
            alpha: Alpha transparency (0-255) for fill colors.
            stroked: Whether to draw polygon outlines.
            get_line_width: Width of polygon outlines.
            get_line_color: RGBA list for outline color. Defaults to [0, 0, 0, 150].
            simplify_tolerance: Optional geometry simplification tolerance in
                degrees. Reduces vertex count for faster rendering.
            view_state: Optional MapViewState to set the initial camera position.
            **layer_kwargs: Additional keyword arguments passed to PolygonLayer.from_geopandas.

        Returns:
            A lonboard Map.
        """
        from lonboard import Map

        layer = self.to_layer(
            alpha=alpha,
            stroked=stroked,
            get_line_width=get_line_width,
            get_line_color=get_line_color,
            simplify_tolerance=simplify_tolerance,
            **layer_kwargs,
        )
        map_kwargs = {"layers": [layer]}
        if view_state is not None:
            map_kwargs["view_state"] = view_state
        return Map(**map_kwargs)

    @staticmethod
    def _parse_biome_code(efg_code):
        """Extract biome code from a functional group code (e.g., 'T1' from 'T1.1')."""
        return efg_code.split('.')[0]

    @staticmethod
    def _parse_realm_code(efg_code):
        """Extract realm code from a functional group code (e.g., 'T' from 'T1.1')."""
        return re.match(r'^[A-Z]+', efg_code).group()

    def _dissolved_layer(self, group_column, style_key, cmap=None, alpha=180,
                         stroked=True, get_line_width=2, get_line_color=None,
                         simplify_tolerance=None, **kwargs):
        """Create a PolygonLayer from geometries dissolved by group_column.

        Args:
            group_column: Column name to dissolve/aggregate by.
            style_key: Key in map_style.yaml ('realms', 'biomes', or 'functional_groups').
            cmap: Optional color map override {value: [r, g, b]}.
            alpha: Alpha transparency (0-255) for fill colors.
            stroked: Whether to draw polygon outlines.
            get_line_width: Width of polygon outlines.
            get_line_color: RGBA list for outline color. Defaults to [0, 0, 0, 150].
            simplify_tolerance: Optional geometry simplification tolerance in degrees.
            **kwargs: Additional keyword arguments passed to PolygonLayer.from_geopandas.

        Returns:
            A lonboard PolygonLayer.
        """
        from lonboard import PolygonLayer
        from lonboard.colormap import apply_categorical_cmap

        if get_line_color is None:
            get_line_color = [0, 0, 0, 150]

        dissolved = self.data.dissolve(by=group_column).reset_index()

        if simplify_tolerance is not None:
            dissolved = self._simplify_geodataframe(dissolved, simplify_tolerance)

        if cmap is None:
            cmap = _load_map_style().get(style_key, {})

        values = dissolved[group_column]
        fill_color = apply_categorical_cmap(values, cmap, alpha=alpha)

        return PolygonLayer.from_geopandas(
            dissolved,
            get_fill_color=fill_color,
            stroked=stroked,
            get_line_width=get_line_width,
            get_line_color=get_line_color,
            **kwargs,
        )

    def _dissolved_map(self, group_column, style_key, cmap=None, alpha=180,
                       stroked=True, get_line_width=2, get_line_color=None,
                       simplify_tolerance=None, view_state=None, **kwargs):
        """Create a Map from geometries dissolved by group_column."""
        from ipywidgets import HBox, Layout
        from lonboard import Map

        layer = self._dissolved_layer(
            group_column, style_key, cmap=cmap, alpha=alpha,
            stroked=stroked, get_line_width=get_line_width,
            get_line_color=get_line_color,
            simplify_tolerance=simplify_tolerance, **kwargs,
        )
        map_kwargs = {"layers": [layer]}
        if view_state is not None:
            map_kwargs["view_state"] = view_state
        m = Map(**map_kwargs)
        m.layout.width = None
        m.layout.flex = '1 1 0px'
        codes = sorted(self.data[group_column].unique())
        legend = _build_legend_widget(style_key, codes)
        return HBox([m, legend], layout=Layout(width='100%'))

    def _ensure_level3_column(self):
        """Raise if get_level3_column is not set."""
        if self.get_level3_column is None:
            raise ValueError(
                "get_level3_column must be specified to use aggregated map views."
            )

    def to_functional_group_layer(self, cmap=None, alpha=180, stroked=True,
                                  get_line_width=2, get_line_color=None,
                                  simplify_tolerance=None, **kwargs):
        """Create a PolygonLayer with geometries dissolved by functional group (GET Level 3).

        Args:
            cmap: Optional color map override {efg_code: [r, g, b]}.
            alpha: Alpha transparency (0-255) for fill colors.
            stroked: Whether to draw polygon outlines.
            get_line_width: Width of polygon outlines.
            get_line_color: RGBA list for outline color. Defaults to [0, 0, 0, 150].
            simplify_tolerance: Optional geometry simplification tolerance in degrees.
            **kwargs: Additional keyword arguments passed to PolygonLayer.from_geopandas.

        Returns:
            A lonboard PolygonLayer.
        """
        self._ensure_level3_column()
        return self._dissolved_layer(
            self.get_level3_column, 'functional_groups', cmap=cmap, alpha=alpha,
            stroked=stroked, get_line_width=get_line_width,
            get_line_color=get_line_color,
            simplify_tolerance=simplify_tolerance, **kwargs,
        )

    def to_functional_group_map(self, cmap=None, alpha=180, stroked=True,
                                get_line_width=2, get_line_color=None,
                                simplify_tolerance=None, view_state=None,
                                **kwargs):
        """Create a Map with geometries dissolved by functional group (GET Level 3).

        Args:
            cmap: Optional color map override {efg_code: [r, g, b]}.
            alpha: Alpha transparency (0-255) for fill colors.
            stroked: Whether to draw polygon outlines.
            get_line_width: Width of polygon outlines.
            get_line_color: RGBA list for outline color. Defaults to [0, 0, 0, 150].
            simplify_tolerance: Optional geometry simplification tolerance in degrees.
            view_state: Optional MapViewState to set the initial camera position.
            **kwargs: Additional keyword arguments passed to PolygonLayer.from_geopandas.

        Returns:
            A lonboard Map.
        """
        self._ensure_level3_column()
        return self._dissolved_map(
            self.get_level3_column, 'functional_groups', cmap=cmap, alpha=alpha,
            stroked=stroked, get_line_width=get_line_width,
            get_line_color=get_line_color,
            simplify_tolerance=simplify_tolerance, view_state=view_state, **kwargs,
        )

    def to_biome_layer(self, cmap=None, alpha=180, stroked=True,
                       get_line_width=2, get_line_color=None,
                       simplify_tolerance=None, **kwargs):
        """Create a PolygonLayer with geometries dissolved by biome (GET Level 2).

        Args:
            cmap: Optional color map override {biome_code: [r, g, b]}.
            alpha: Alpha transparency (0-255) for fill colors.
            stroked: Whether to draw polygon outlines.
            get_line_width: Width of polygon outlines.
            get_line_color: RGBA list for outline color. Defaults to [0, 0, 0, 150].
            simplify_tolerance: Optional geometry simplification tolerance in degrees.
            **kwargs: Additional keyword arguments passed to PolygonLayer.from_geopandas.

        Returns:
            A lonboard PolygonLayer.
        """
        self._ensure_level3_column()
        self.data['_biome'] = self.data[self.get_level3_column].map(self._parse_biome_code)
        try:
            return self._dissolved_layer(
                '_biome', 'biomes', cmap=cmap, alpha=alpha,
                stroked=stroked, get_line_width=get_line_width,
                get_line_color=get_line_color,
                simplify_tolerance=simplify_tolerance, **kwargs,
            )
        finally:
            self.data.drop(columns='_biome', inplace=True)

    def to_biome_map(self, cmap=None, alpha=180, stroked=True,
                     get_line_width=2, get_line_color=None,
                     simplify_tolerance=None, view_state=None, **kwargs):
        """Create a Map with geometries dissolved by biome (GET Level 2).

        Args:
            cmap: Optional color map override {biome_code: [r, g, b]}.
            alpha: Alpha transparency (0-255) for fill colors.
            stroked: Whether to draw polygon outlines.
            get_line_width: Width of polygon outlines.
            get_line_color: RGBA list for outline color. Defaults to [0, 0, 0, 150].
            simplify_tolerance: Optional geometry simplification tolerance in degrees.
            view_state: Optional MapViewState to set the initial camera position.
            **kwargs: Additional keyword arguments passed to PolygonLayer.from_geopandas.

        Returns:
            A lonboard Map.
        """
        self._ensure_level3_column()
        self.data['_biome'] = self.data[self.get_level3_column].map(self._parse_biome_code)
        try:
            return self._dissolved_map(
                '_biome', 'biomes', cmap=cmap, alpha=alpha,
                stroked=stroked, get_line_width=get_line_width,
                get_line_color=get_line_color,
                simplify_tolerance=simplify_tolerance, view_state=view_state,
                **kwargs,
            )
        finally:
            self.data.drop(columns='_biome', inplace=True)

    def to_realm_layer(self, cmap=None, alpha=180, stroked=True,
                       get_line_width=2, get_line_color=None,
                       simplify_tolerance=None, **kwargs):
        """Create a PolygonLayer with geometries dissolved by realm (GET Level 1).

        Args:
            cmap: Optional color map override {realm_code: [r, g, b]}.
            alpha: Alpha transparency (0-255) for fill colors.
            stroked: Whether to draw polygon outlines.
            get_line_width: Width of polygon outlines.
            get_line_color: RGBA list for outline color. Defaults to [0, 0, 0, 150].
            simplify_tolerance: Optional geometry simplification tolerance in degrees.
            **kwargs: Additional keyword arguments passed to PolygonLayer.from_geopandas.

        Returns:
            A lonboard PolygonLayer.
        """
        self._ensure_level3_column()
        self.data['_realm'] = self.data[self.get_level3_column].map(self._parse_realm_code)
        try:
            return self._dissolved_layer(
                '_realm', 'realms', cmap=cmap, alpha=alpha,
                stroked=stroked, get_line_width=get_line_width,
                get_line_color=get_line_color,
                simplify_tolerance=simplify_tolerance, **kwargs,
            )
        finally:
            self.data.drop(columns='_realm', inplace=True)

    def to_realm_map(self, cmap=None, alpha=180, stroked=True,
                     get_line_width=2, get_line_color=None,
                     simplify_tolerance=None, view_state=None, **kwargs):
        """Create a Map with geometries dissolved by realm (GET Level 1).

        Args:
            cmap: Optional color map override {realm_code: [r, g, b]}.
            alpha: Alpha transparency (0-255) for fill colors.
            stroked: Whether to draw polygon outlines.
            get_line_width: Width of polygon outlines.
            get_line_color: RGBA list for outline color. Defaults to [0, 0, 0, 150].
            simplify_tolerance: Optional geometry simplification tolerance in degrees.
            view_state: Optional MapViewState to set the initial camera position.
            **kwargs: Additional keyword arguments passed to PolygonLayer.from_geopandas.

        Returns:
            A lonboard Map.
        """
        self._ensure_level3_column()
        self.data['_realm'] = self.data[self.get_level3_column].map(self._parse_realm_code)
        try:
            return self._dissolved_map(
                '_realm', 'realms', cmap=cmap, alpha=alpha,
                stroked=stroked, get_line_width=get_line_width,
                get_line_color=get_line_color,
                simplify_tolerance=simplify_tolerance, view_state=view_state,
                **kwargs,
            )
        finally:
            self.data.drop(columns='_realm', inplace=True)

    @abstractmethod
    def _get_feature_count(self) -> int:
        """Return the number of features in the dataset."""
        ...

    @abstractmethod
    def _get_preview_rows(self, n: int = 5) -> tuple[list[str], list[dict]]:
        """Return (column_names, rows_as_dicts) for the first n features."""
        ...

    def _data_repr_html_(self, meta_rows: list[str]) -> str:
        """Shared vector HTML rendering with highlighted GET columns."""
        if self.get_level3_column:
            meta_rows.append(f"<tr><td><b>GET Level 3 Column</b></td><td>{self.get_level3_column}</td></tr>")
        if self.get_level456_column:
            meta_rows.append(f"<tr><td><b>GET Level 4 Column</b></td><td>{self.get_level456_column}</td></tr>")

        count = self._get_feature_count()
        meta_rows.append(f"<tr><td><b>Feature Count</b></td><td>{count}</td></tr>")

        props, rows = self._get_preview_rows(5)
        if not rows or not props:
            return ""

        # Build header row with highlight for GET columns
        header_cells = []
        for p in props:
            if p == self.get_level3_column:
                header_cells.append(f'<th style="padding: 4px 8px; border: 1px solid #ddd; background-color: #cce5ff; font-weight: bold;">{p}</th>')
            elif p == self.get_level456_column:
                header_cells.append(f'<th style="padding: 4px 8px; border: 1px solid #ddd; background-color: #d4edda; font-weight: bold;">{p}</th>')
            else:
                header_cells.append(f'<th style="padding: 4px 8px; border: 1px solid #ddd; background-color: #f5f5f5;">{p}</th>')
        header_row = f'<tr>{"".join(header_cells)}</tr>'

        # Build data rows with highlight for GET columns
        data_rows = []
        for row in rows:
            cells = []
            for p in props:
                val = row.get(p, "")
                if p == self.get_level3_column:
                    cells.append(f'<td style="padding: 4px 8px; border: 1px solid #ddd; background-color: #cce5ff;">{val}</td>')
                elif p == self.get_level456_column:
                    cells.append(f'<td style="padding: 4px 8px; border: 1px solid #ddd; background-color: #d4edda;">{val}</td>')
                else:
                    cells.append(f'<td style="padding: 4px 8px; border: 1px solid #ddd;">{val}</td>')
            data_rows.append(f'<tr>{"".join(cells)}</tr>')

        more_text = f"<p style='color: #666; font-style: italic;'>Showing {len(rows)} of {count} records</p>" if count > len(rows) else ""

        return f"""
        <h4 style="margin-top: 16px; margin-bottom: 8px;">Records</h4>
        <table style="border-collapse: collapse; margin-top: 8px;">
            <thead>{header_row}</thead>
            <tbody>{''.join(data_rows)}</tbody>
        </table>
        {more_text}
        """


class RasterMap(EcosystemMap):
    """Intermediate base for raster ecosystem map backends.

    Provides shared attributes and HTML rendering for raster data with
    an ecosystem band and data dictionary.

    Attributes:
        ecosystem_band: Name of the categorical band containing ecosystem IDs.
        ecosystem_dataframe: DataFrame mapping ecosystem IDs to GET codes.
    """

    ecosystem_band: str
    ecosystem_dataframe: "pd.DataFrame"

    @abstractmethod
    def _get_band_names(self) -> list[str]:
        """Return the list of band/variable names in the dataset."""
        ...

    def functional_group_dataframe(self) -> "pd.DataFrame":
        """Return the ecosystem data dictionary as a pandas DataFrame."""
        return self.ecosystem_dataframe

    def _data_repr_html_(self, meta_rows: list[str]) -> str:
        """Shared raster HTML rendering for ecosystem data dictionary."""
        bands = self._get_band_names()
        meta_rows.append(f"<tr><td><b>Bands</b></td><td>{', '.join(bands)}</td></tr>")
        meta_rows.append(f"<tr><td><b>Ecosystem Band</b></td><td>{self.ecosystem_band}</td></tr>")

        df = self.ecosystem_dataframe
        preview_rows = min(5, len(df))

        if preview_rows == 0:
            return ""

        # Build header row
        header_cells = [f'<th style="padding: 4px 8px; border: 1px solid #ddd; background-color: #f5f5f5;">{df.index.name or "ecosystem_id"}</th>']
        for col in df.columns:
            header_cells.append(f'<th style="padding: 4px 8px; border: 1px solid #ddd; background-color: #f5f5f5;">{col}</th>')
        header_row = f'<tr>{"".join(header_cells)}</tr>'

        # Build data rows
        data_rows = []
        for idx, row in df.head(preview_rows).iterrows():
            cells = [f'<td style="padding: 4px 8px; border: 1px solid #ddd;">{idx}</td>']
            for val in row:
                cells.append(f'<td style="padding: 4px 8px; border: 1px solid #ddd;">{val}</td>')
            data_rows.append(f'<tr>{"".join(cells)}</tr>')

        more_text = f"<p style='color: #666; font-style: italic;'>Showing 5 of {len(df)} records</p>" if len(df) > 5 else ""

        return f"""
        <h4 style="margin-top: 16px; margin-bottom: 8px;">Ecosystem Data Dictionary</h4>
        <table style="border-collapse: collapse; margin-top: 8px;">
            <thead>{header_row}</thead>
            <tbody>{''.join(data_rows)}</tbody>
        </table>
        {more_text}
        """
