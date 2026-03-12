"""Earth Engine vector backend for ecosystem maps."""

from typing import TYPE_CHECKING

from ipywidgets import Output, GridBox, Layout

from . import EcosystemBackendEntrypoint
from ._ee_common import _require_ee, _is_file_path, _get_cached_asset_type, _resolve_data
from ..ecosystem_map import VectorMap

if TYPE_CHECKING:
    import pandas as pd


class ClickableMap(GridBox):
    """A lonboard Map with an EE click-to-query overlay panel.

    Attributes:
        map: The underlying lonboard.Map widget.
    """

    def __init__(self, map_widget, output_widget):
        map_widget.layout = Layout(
            grid_area="map", width="100%", height="100%", z_index="0",
        )
        output_widget.layout = Layout(
            grid_area="map",
            align_self="center",
            max_height="50%",
            max_width="400px",
            overflow_y="auto",
            z_index="9999",
        )
        super().__init__(
            [map_widget, output_widget],
            layout=Layout(
                width="100%",
                height="500px",
                grid_template_areas='"map"',
                grid_template_columns="1fr",
                grid_template_rows="1fr",
            ),
        )
        self.map = map_widget


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

    @staticmethod
    def _ee_bitmap_tile_layer(tile_url):
        """Create a BitmapTileLayer from an EE tile URL."""
        from lonboard import BitmapTileLayer

        return BitmapTileLayer(
            data=tile_url,
            tile_size=256,
            max_requests=-1,
            min_zoom=0,
            max_zoom=19,
        )

    def to_layer(self, alpha=180, stroked=True, get_line_width=2,
                 get_line_color=None, simplify_tolerance=None, **kwargs):
        """Create a lonboard BitmapTileLayer from this Earth Engine ecosystem map.

        Paints the FeatureCollection into an ee.Image and renders via EE
        tile URLs, avoiding client-side geometry download.

        Args:
            alpha: Alpha transparency (0-255) for fill colors.
            stroked: Whether to draw polygon outlines.
            **kwargs: Ignored (kept for signature compatibility).

        Returns:
            A lonboard BitmapTileLayer.
        """
        ee = _require_ee()
        fc = self.data
        opacity = alpha / 255.0

        if self.cmap is not None and self.get_level456_column is not None:
            # Colored by category using cmap
            codes = sorted(self.cmap.keys())
            ids = list(range(1, len(codes) + 1))
            palette = [
                '#{:02x}{:02x}{:02x}'.format(*self.cmap[code])
                for code in codes
            ]
            fc_remapped = fc.remap(codes, ids, self.get_level456_column)
            image = (
                ee.Image().byte()
                .paint(featureCollection=fc_remapped, color=self.get_level456_column)
                .selfMask()
            )
            tile_url = image.getMapId(vis_params={
                'min': 1,
                'max': len(codes),
                'palette': palette,
                'opacity': opacity,
            })['tile_fetcher'].url_format
        else:
            # Grey fill + black outline
            fc_fill = ee.Image().byte().paint(featureCollection=fc, color=1)
            fc_outline = ee.Image().byte().paint(
                featureCollection=fc, color=1, width=get_line_width if stroked else 0,
            )
            fill_styled = fc_fill.selfMask().visualize(
                palette=['808080'], opacity=opacity,
            )
            outline_styled = fc_outline.selfMask().visualize(
                palette=['000000'], opacity=1.0,
            )
            styled_image = ee.ImageCollection(
                [fill_styled, outline_styled]
            ).mosaic()
            tile_url = styled_image.getMapId()['tile_fetcher'].url_format

        return self._ee_bitmap_tile_layer(tile_url)

    def _dissolved_layer(self, group_column, style_key, cmap=None, alpha=180,
                         stroked=True, get_line_width=2, get_line_color=None,
                         simplify_tolerance=None, **kwargs):
        """Create a BitmapTileLayer from EE features colored by group_column.

        Uses server-side remap + paint to color features by category,
        with palette from map_style.yaml or the provided cmap.

        Returns:
            A tuple of (lonboard BitmapTileLayer, list of category codes).
        """
        ee = _require_ee()
        from ..ecosystem_map import _load_map_style

        fc = self.data
        opacity = alpha / 255.0

        # Get unique values for the group column
        codes = sorted(
            fc.aggregate_array(group_column).distinct().getInfo()
        )
        ids = list(range(1, len(codes) + 1))

        # Build palette
        if cmap is None:
            cmap = _load_map_style().get(style_key, {})
        palette = [
            '#{:02x}{:02x}{:02x}'.format(*cmap.get(code, [128, 128, 128]))
            for code in codes
        ]

        fc_remapped = fc.remap(codes, ids, group_column)
        image = (
            ee.Image().byte()
            .paint(featureCollection=fc_remapped, color=group_column)
            .selfMask()
        )
        tile_url = image.getMapId(vis_params={
            'min': 1,
            'max': len(codes),
            'palette': palette,
            'opacity': opacity,
        })['tile_fetcher'].url_format

        return self._ee_bitmap_tile_layer(tile_url), codes

    def _add_derived_column(self, derived_name, parser_func):
        """Add a server-side derived column to the FeatureCollection.

        Args:
            derived_name: Name for the new property (e.g., '_biome', '_realm').
            parser_func: A static method like _parse_biome_code or _parse_realm_code.

        Returns:
            An ee.FeatureCollection with the derived column added.
        """
        ee = _require_ee()
        col = self.get_level3_column

        if parser_func == self._parse_biome_code:
            # Extract biome code: everything before the first '.'
            def derive(feature):
                val = ee.String(ee.Feature(feature).get(col))
                return ee.Feature(feature).set(
                    derived_name, val.split('\\.').get(0)
                )
        else:
            # Extract realm code: leading uppercase letters
            def derive(feature):
                val = ee.String(ee.Feature(feature).get(col))
                return ee.Feature(feature).set(
                    derived_name, val.match('^[A-Z]+').get(0)
                )

        return self.data.map(derive)

    def _make_click_handler(self, output_widget):
        """Return a click callback that queries EE and displays feature properties."""
        ee = _require_ee()
        fc = self.data

        def _on_click(coord):
            lon, lat = coord
            output_widget.clear_output(wait=True)
            with output_widget:
                from IPython.display import display, HTML
                display(HTML("<i>Querying...</i>"))

            try:
                point = ee.Geometry.Point([lon, lat])
                info = fc.filterBounds(point).first().getInfo()
            except Exception:
                info = None

            output_widget.clear_output(wait=True)
            with output_widget:
                from IPython.display import display, HTML
                if info is None:
                    display(HTML(
                        f'<div style="background:white;border-radius:4px;'
                        f'box-shadow:0 2px 8px rgba(0,0,0,0.3);padding:8px;margin:8px">'
                        f'<i>No feature found at ({lon:.4f}, {lat:.4f})</i></div>'
                    ))
                    return
                props = info.get('properties', {})
                rows = ''.join(
                    f'<tr><td style="padding:2px 8px;font-weight:bold">{k}</td>'
                    f'<td style="padding:2px 8px">{v}</td></tr>'
                    for k, v in props.items()
                )
                display(HTML(
                    f'<div style="background:white;border-radius:4px;'
                    f'box-shadow:0 2px 8px rgba(0,0,0,0.3);padding:8px;margin:8px">'
                    f'<b>Feature at ({lon:.4f}, {lat:.4f})</b>'
                    f'<table style="border-collapse:collapse;margin-top:4px">'
                    f'{rows}</table></div>'
                ))

        return _on_click

    def _attach_click_popup(self, map_widget):
        """Attach an EE click-query popup to a lonboard Map.

        Returns:
            A ClickableMap (VBox) containing the Map and an output area.
        """
        output = Output()
        map_widget.on_click(self._make_click_handler(output))
        return ClickableMap(map_widget, output)

    def to_map(self, alpha=180, stroked=True, get_line_width=2,
               get_line_color=None, simplify_tolerance=None,
               view_state=None, **layer_kwargs):
        """Create a ClickableMap displaying this Earth Engine ecosystem map.

        Clicking on the map queries Earth Engine for the feature at that
        location and displays its properties below the map.

        Args:
            alpha: Alpha transparency (0-255) for fill colors.
            stroked: Whether to draw polygon outlines.
            get_line_width: Width of polygon outlines.
            get_line_color: RGBA list for outline color.
            simplify_tolerance: Ignored for EE backend.
            view_state: Optional MapViewState to set the initial camera position.
            **layer_kwargs: Additional keyword arguments.

        Returns:
            A ClickableMap. Access the lonboard.Map via .map attribute.
        """
        from lonboard import Map

        layer = self.to_layer(
            alpha=alpha, stroked=stroked,
            get_line_width=get_line_width, get_line_color=get_line_color,
            simplify_tolerance=simplify_tolerance, **layer_kwargs,
        )
        map_kwargs = {"layers": [layer]}
        if view_state is not None:
            map_kwargs["view_state"] = view_state
        return self._attach_click_popup(Map(**map_kwargs))

    def to_biome_layer(self, cmap=None, alpha=180, stroked=True,
                       get_line_width=2, get_line_color=None,
                       simplify_tolerance=None, **kwargs):
        """Create a BitmapTileLayer with features colored by biome (GET Level 2).

        Returns:
            A tuple of (lonboard BitmapTileLayer, list of biome codes).
        """
        self._ensure_level3_column()
        fc_with_biome = self._add_derived_column('_biome', self._parse_biome_code)
        original_data = self.data
        self.data = fc_with_biome
        try:
            return self._dissolved_layer(
                '_biome', 'biomes', cmap=cmap, alpha=alpha,
                stroked=stroked, get_line_width=get_line_width,
                get_line_color=get_line_color,
                simplify_tolerance=simplify_tolerance, **kwargs,
            )
        finally:
            self.data = original_data

    def to_biome_map(self, cmap=None, alpha=180, stroked=True,
                     get_line_width=2, get_line_color=None,
                     simplify_tolerance=None, view_state=None, **kwargs):
        """Create a ClickableMap with features colored by biome (GET Level 2)."""
        from ipywidgets import HBox, Layout
        from lonboard import Map
        from ..ecosystem_map import _build_legend_widget

        layer, codes = self.to_biome_layer(
            cmap=cmap, alpha=alpha, stroked=stroked,
            get_line_width=get_line_width, get_line_color=get_line_color,
            simplify_tolerance=simplify_tolerance, **kwargs,
        )
        map_kwargs = {"layers": [layer]}
        if view_state is not None:
            map_kwargs["view_state"] = view_state
        clickable = self._attach_click_popup(Map(**map_kwargs))
        clickable.layout.width = None
        clickable.layout.flex = '1 1 0px'
        legend = _build_legend_widget('biomes', codes)
        return HBox([clickable, legend], layout=Layout(width='100%'))

    def to_realm_layer(self, cmap=None, alpha=180, stroked=True,
                       get_line_width=2, get_line_color=None,
                       simplify_tolerance=None, **kwargs):
        """Create a BitmapTileLayer with features colored by realm (GET Level 1).

        Returns:
            A tuple of (lonboard BitmapTileLayer, list of realm codes).
        """
        self._ensure_level3_column()
        fc_with_realm = self._add_derived_column('_realm', self._parse_realm_code)
        original_data = self.data
        self.data = fc_with_realm
        try:
            return self._dissolved_layer(
                '_realm', 'realms', cmap=cmap, alpha=alpha,
                stroked=stroked, get_line_width=get_line_width,
                get_line_color=get_line_color,
                simplify_tolerance=simplify_tolerance, **kwargs,
            )
        finally:
            self.data = original_data

    def to_realm_map(self, cmap=None, alpha=180, stroked=True,
                     get_line_width=2, get_line_color=None,
                     simplify_tolerance=None, view_state=None, **kwargs):
        """Create a ClickableMap with features colored by realm (GET Level 1)."""
        from ipywidgets import HBox, Layout
        from lonboard import Map
        from ..ecosystem_map import _build_legend_widget

        layer, codes = self.to_realm_layer(
            cmap=cmap, alpha=alpha, stroked=stroked,
            get_line_width=get_line_width, get_line_color=get_line_color,
            simplify_tolerance=simplify_tolerance, **kwargs,
        )
        map_kwargs = {"layers": [layer]}
        if view_state is not None:
            map_kwargs["view_state"] = view_state
        clickable = self._attach_click_popup(Map(**map_kwargs))
        clickable.layout.width = None
        clickable.layout.flex = '1 1 0px'
        legend = _build_legend_widget('realms', codes)
        return HBox([clickable, legend], layout=Layout(width='100%'))

    def to_functional_group_map(self, cmap=None, alpha=180, stroked=True,
                                get_line_width=2, get_line_color=None,
                                simplify_tolerance=None, view_state=None,
                                **kwargs):
        """Create a ClickableMap with features colored by functional group (GET Level 3)."""
        from ipywidgets import HBox, Layout
        from lonboard import Map
        from ..ecosystem_map import _build_legend_widget

        self._ensure_level3_column()
        layer, codes = self.to_functional_group_layer(
            cmap=cmap, alpha=alpha, stroked=stroked,
            get_line_width=get_line_width, get_line_color=get_line_color,
            simplify_tolerance=simplify_tolerance, **kwargs,
        )
        map_kwargs = {"layers": [layer]}
        if view_state is not None:
            map_kwargs["view_state"] = view_state
        clickable = self._attach_click_popup(Map(**map_kwargs))
        clickable.layout.width = None
        clickable.layout.flex = '1 1 0px'
        legend = _build_legend_widget('functional_groups', codes)
        return HBox([clickable, legend], layout=Layout(width='100%'))

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
