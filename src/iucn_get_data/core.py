import re
import yaml
from dataclasses import dataclass, field
from importlib import resources
from importlib.metadata import version
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


@dataclass
class FunctionalGroup:
    """
    Level 3 of the IUCN Global Ecosystem Typology: Ecosystem Functional Group.

    Ecosystem Functional Groups (EFGs) are groups of related ecosystems within a
    biome that share common ecological drivers, ecological traits, and assembly
    processes. There are 109 EFGs in GET 2.0.

    See: https://global-ecosystems.org/

    Attributes:
        code: Unique identifier (e.g., 'T1.1', 'M2.3').
        name: Descriptive name of the functional group.
        description: Detailed description of ecosystem characteristics.
        url: URL to the functional group page on global-ecosystems.org.
        biome_code: Code of the parent biome (e.g., 'T1').
        realm_code: Code of the parent realm (e.g., 'T').
    """
    code: str
    name: str
    description: str
    url: str
    biome_code: str = None
    realm_code: str = None


@dataclass
class Biome:
    """
    Level 2 of the IUCN Global Ecosystem Typology: Biome.

    Biomes are components of realms united by broad features of ecosystem
    structure and one or more major ecological drivers. They include both
    traditional biomes (e.g., tropical forests, temperate grasslands) and
    functionally distinctive groupings like lentic/lotic freshwater systems,
    pelagic/benthic marine systems, and anthropogenic ecosystems.
    There are 25 biomes in GET 2.0.

    See: https://global-ecosystems.org/

    Attributes:
        code: Unique identifier (e.g., 'T1', 'M2', 'MT1').
        name: Descriptive name of the biome.
        description: Detailed description of biome characteristics.
        url: URL to the biome page on global-ecosystems.org.
        functional_groups: Dictionary of child EFGs keyed by code.
        realm_code: Code of the parent realm.
    """
    code: str
    name: str
    description: str
    url: str
    functional_groups: dict[str, FunctionalGroup] = field(default_factory=dict)
    realm_code: str = None


@dataclass
class Realm:
    """
    Level 1 of the IUCN Global Ecosystem Typology: Realm.

    Realms are the highest level of ecosystem classification, distinguished
    by the major environmental factors that shape ecosystem properties. GET 2.0
    includes 4 core realms (Terrestrial, Freshwater, Marine, Subterranean) and
    6 transitional realms at their interfaces (e.g., Marine-Terrestrial).

    See: https://global-ecosystems.org/

    Attributes:
        code: Unique identifier (e.g., 'T', 'M', 'F', 'S', 'MT').
        name: Descriptive name of the realm.
        description: Detailed description of realm characteristics.
        transitional: True if this is a transitional realm between core realms.
        url: URL to the realm page on global-ecosystems.org.
        biomes: Dictionary of child biomes keyed by code.
    """
    code: str
    name: str
    description: str
    transitional: bool
    url: str
    biomes: dict[str, Biome] = field(default_factory=dict)


@dataclass
class Typology:
    """
    The IUCN Global Ecosystem Typology (GET) 2.0.

    A comprehensive, hierarchical classification framework for Earth's ecosystems
    that integrates their functional and compositional features. Developed by the
    IUCN Commission on Ecosystem Management, GET supports applications from global
    to local scales for biodiversity conservation, research, and ecosystem management.

    The typology comprises six hierarchical levels:
    - Upper levels (function-based): Realms → Biomes → Ecosystem Functional Groups
    - Lower levels (composition-based): Biogeographic ecotypes → Global ecosystem types → Subglobal types

    This library provides access to the three upper levels:
    - 10 Realms (4 core + 6 transitional)
    - 25 Biomes
    - 109 Ecosystem Functional Groups

    See: https://global-ecosystems.org/

    Attributes:
        language: Language for typology data (default: "english").
        realms: Dictionary of realms keyed by their code.
        ecosystems: Optional DataFrame containing ecosystem records.
        ecosystems_functional_group_column: Column name for functional group codes in ecosystems.

    Example:
        >>> typology = Typology()  # Uses English
        >>> typology = Typology(language="spanish")  # Uses Spanish
        >>> typology = Typology(ecosystems=df, ecosystems_functional_group_column='efg_code')
    """
    language: str = "english"
    realms: dict[str, Realm] = field(default_factory=dict)
    ecosystems: "pd.DataFrame" = None
    ecosystems_functional_group_column: str = None

    def __post_init__(self):
        """Load typology data if realms not provided."""
        if not self.realms:
            data = _load_yaml(language=self.language)
            self.realms = _build_realms(data)

        # Validate ecosystems column if provided
        if self.ecosystems is not None and self.ecosystems_functional_group_column is None:
            raise ValueError("ecosystems_functional_group_column required when ecosystems is provided")
        if self.ecosystems is not None:
            valid_names = list(self.ecosystems.columns) + list(self.ecosystems.index.names)
            if self.ecosystems_functional_group_column not in valid_names:
                raise ValueError(f"Column '{self.ecosystems_functional_group_column}' not found in ecosystems DataFrame columns or index")

    def get_biomes(self, realm: str = None) -> dict[str, Biome]:
        """
        Get biomes, optionally filtered by realm.

        Args:
            realm: Optional realm code to filter biomes (e.g., 'T', 'M', 'F', 'S', 'TF', etc.)
                   If None, returns all biomes from all realms.

        Returns:
            dict: Dictionary with biome codes as keys and Biome instances as values
        """
        if realm is not None:
            if realm not in self.realms:
                raise ValueError(f"Realm '{realm}' not found. Valid realms: {', '.join(self.realms.keys())}")
            return self.realms[realm].biomes

        # Return all biomes from all realms
        all_biomes = {}
        for r in self.realms.values():
            all_biomes.update(r.biomes)
        return all_biomes

    def get_groups(self, realm: str = None, biome: str = None) -> dict[str, FunctionalGroup]:
        """
        Get functional groups, optionally filtered by realm and/or biome.

        Args:
            realm: Optional realm code to filter functional groups
            biome: Optional biome code to filter functional groups

        Returns:
            dict: Dictionary with functional group codes as keys and FunctionalGroup instances as values
        """
        # If biome is specified, extract realm from biome code if not provided
        if biome is not None and realm is None:
            match = re.match(r'^([A-Z]+)(\d+)$', biome)
            if match:
                realm = match.group(1)
            else:
                raise ValueError(f"Invalid biome code format: '{biome}'")

        # Filter realms if specified
        if realm is not None:
            if realm not in self.realms:
                raise ValueError(f"Realm '{realm}' not found. Valid realms: {', '.join(self.realms.keys())}")
            realms_to_search = {realm: self.realms[realm]}
        else:
            realms_to_search = self.realms

        # Collect functional groups
        all_groups = {}
        for r in realms_to_search.values():
            for b in r.biomes.values():
                if biome is not None and b.code != biome:
                    continue
                all_groups.update(b.functional_groups)

        # If biome was specified but no groups found, raise error
        if biome is not None and not all_groups:
            raise ValueError(f"Biome '{biome}' not found in realm '{realm}'")

        return all_groups

    def add_ecosystems(self, data: "pd.DataFrame", functional_group_column: str) -> None:
        """
        Add ecosystem data to be merged with typology.

        Args:
            data: DataFrame containing ecosystem records.
            functional_group_column: Name of column or index level containing functional group codes.

        Example:
            >>> typology = Typology(language="spanish")
            >>> typology.add_ecosystems(ecosystems_df, functional_group_column='efg_code')
            >>> typology.dataframe  # Returns merged data
        """
        # Check both columns and index names
        valid_names = list(data.columns) + list(data.index.names)
        if functional_group_column not in valid_names:
            raise ValueError(f"Column '{functional_group_column}' not found in DataFrame columns or index")

        self.ecosystems = data
        self.ecosystems_functional_group_column = functional_group_column

    @property
    def dataframe(self):
        """
        Return typology as a pandas DataFrame, merged with ecosystems if added.

        When no ecosystems are added, returns a DataFrame with all functional groups,
        indexed by (realm_code, biome_code, functional_group_code).

        When ecosystems are added, returns a merged DataFrame with typology and
        ecosystem data.

        Returns:
            pandas.DataFrame: DataFrame with typology data, optionally merged with ecosystems.
        """
        import pandas as pd

        rows = []
        for realm in self.realms.values():
            for biome in realm.biomes.values():
                for fg in biome.functional_groups.values():
                    rows.append({
                        'realm_code': realm.code,
                        'biome_code': biome.code,
                        'functional_group_code': fg.code,
                        'realm_name': realm.name,
                        'biome_name': biome.name,
                        'functional_group_name': fg.name,
                        'description': fg.description,
                        'url': fg.url,
                    })

        df = pd.DataFrame(rows)
        df = df.set_index(['realm_code', 'biome_code', 'functional_group_code'])

        # Merge with ecosystems if added
        if self.ecosystems is not None:
            # Reset ecosystems index to preserve it as columns in the merge
            ecosystems_df = self.ecosystems.reset_index()
            df = df.reset_index().merge(
                ecosystems_df,
                left_on='functional_group_code',
                right_on=self.ecosystems_functional_group_column,
                how='right'
            )

        return df

    def as_html(
        self,
        ecosystem_columns: list[str] = None,
        drop_columns: list[str] = None,
        hide_empty: bool = True,
        ecosystem_name_column: str = None,
        ecosystem_id_column: str = None
    ) -> str:
        """
        Return typology as an HTML table with hierarchical row-based structure.

        The table displays realm → biome → functional group → ecosystem hierarchy
        with each level on its own row spanning all columns.

        Args:
            ecosystem_columns: List of column names to display for ecosystems.
                              If None and ecosystems are added, uses all non-typology columns.
            drop_columns: List of column names to exclude from display.
            hide_empty: If True (default), hide realm, biome, and functional group
                       headings that don't contain any ecosystems.
            ecosystem_name_column: Column containing ecosystem names (displayed first).
            ecosystem_id_column: Column containing ecosystem IDs (displayed second).

        Returns:
            str: HTML string containing the hierarchical table.
        """
        # Define realm order
        realm_order = ['T', 'M', 'F', 'S', 'MT', 'SF', 'FM', 'MFT', 'SM', 'TF']

        # Determine ecosystem columns to display
        eco_cols = []
        drop_set = set(drop_columns) if drop_columns else set()
        if self.ecosystems is not None:
            df = self.dataframe
            typology_cols = {'realm_code', 'biome_code', 'functional_group_code',
                            'realm_name', 'biome_name', 'functional_group_name',
                            'description', 'url', self.ecosystems_functional_group_column}
            if ecosystem_columns is None:
                available_cols = [col for col in df.columns if col not in typology_cols and col not in drop_set]
                # Order columns: name first, then ID, then remaining
                ordered_cols = []
                if ecosystem_name_column and ecosystem_name_column in available_cols:
                    ordered_cols.append(ecosystem_name_column)
                    available_cols.remove(ecosystem_name_column)
                if ecosystem_id_column and ecosystem_id_column in available_cols:
                    ordered_cols.append(ecosystem_id_column)
                    available_cols.remove(ecosystem_id_column)
                eco_cols = ordered_cols + available_cols
            else:
                eco_cols = [col for col in ecosystem_columns if col not in drop_set]

        # Calculate column count for spanning
        num_cols = max(len(eco_cols), 1)

        rows = []
        rows.append('<table class="typology-table" style="border-collapse: collapse; width: 100%;">')

        # Add header if ecosystems present
        if eco_cols:
            rows.append('<thead><tr>')
            for col in eco_cols:
                rows.append(f'<th style="border: 1px solid #ddd; padding: 8px; text-align: left;">{col}</th>')
            rows.append('</tr></thead>')

        rows.append('<tbody>')

        # Build ecosystem lookup if ecosystems are added
        ecosystem_lookup = {}
        if self.ecosystems is not None and eco_cols:
            df = self.dataframe
            for _, row in df.iterrows():
                fg_code = row['functional_group_code']
                if fg_code not in ecosystem_lookup:
                    ecosystem_lookup[fg_code] = []
                ecosystem_lookup[fg_code].append({col: row[col] for col in eco_cols})

        # Sort realms by defined order
        sorted_realm_codes = sorted(
            self.realms.keys(),
            key=lambda x: realm_order.index(x) if x in realm_order else len(realm_order)
        )

        for realm_code in sorted_realm_codes:
            realm = self.realms[realm_code]

            # Check if realm has any ecosystems (for hide_empty)
            if hide_empty:
                realm_has_ecosystems = any(
                    ecosystem_lookup.get(fg_code)
                    for biome in realm.biomes.values()
                    for fg_code in biome.functional_groups.keys()
                )
                if not realm_has_ecosystems:
                    continue

            # Realm row - grey background, spans all columns
            rows.append('<tr>')
            rows.append(f'<td colspan="{num_cols}" style="background-color: #e0e0e0; padding: 8px; font-weight: bold; text-align: left;">'
                       f'REALM: {realm.name} ({realm_code})</td>')
            rows.append('</tr>')

            # Sort biomes by code
            sorted_biome_codes = sorted(realm.biomes.keys())

            for biome_code in sorted_biome_codes:
                biome = realm.biomes[biome_code]

                # Check if biome has any ecosystems (for hide_empty)
                if hide_empty:
                    biome_has_ecosystems = any(
                        ecosystem_lookup.get(fg_code)
                        for fg_code in biome.functional_groups.keys()
                    )
                    if not biome_has_ecosystems:
                        continue

                # Biome row - white background, spans all columns
                rows.append('<tr>')
                rows.append(f'<td colspan="{num_cols}" style="background-color: #ffffff; padding: 8px; font-weight: bold; text-align: left;">'
                           f'{biome.name} ({biome_code})</td>')
                rows.append('</tr>')

                # Sort functional groups by code
                sorted_fg_codes = sorted(biome.functional_groups.keys())

                for fg_code in sorted_fg_codes:
                    fg = biome.functional_groups[fg_code]

                    # Get ecosystems for this functional group
                    ecosystems_list = ecosystem_lookup.get(fg_code, [])

                    # Skip if hide_empty and no ecosystems
                    if hide_empty and not ecosystems_list:
                        continue

                    # Functional group row - white background, single indent
                    rows.append('<tr>')
                    rows.append(f'<td colspan="{num_cols}" style="background-color: #ffffff; padding: 8px 8px 8px 24px; text-align: left;">'
                               f'{fg.name} ({fg_code})</td>')
                    rows.append('</tr>')

                    # Ecosystem rows - two level indent (48px = 2 × 24px), white background
                    for eco in ecosystems_list:
                        rows.append('<tr style="background-color: #ffffff !important;">')
                        for i, col in enumerate(eco_cols):
                            # First column gets two-level indent for hierarchy
                            if i == 0:
                                rows.append(f'<td style="background-color: #ffffff !important; border: 1px solid #ddd; padding: 8px 8px 8px 48px; text-align: left;">{eco.get(col, "")}</td>')
                            else:
                                rows.append(f'<td style="background-color: #ffffff !important; border: 1px solid #ddd; padding: 8px; text-align: left;">{eco.get(col, "")}</td>')
                        rows.append('</tr>')

        rows.append('</tbody></table>')
        return '\n'.join(rows)


def _get_default_typology_path(language="english"):
    """Get the path to the bundled YAML file."""
    return resources.files("iucn_get_data").joinpath(f"data/{language}.yaml")


def _load_yaml(language="english"):
    """Load YAML data from the bundled file for the specified language."""
    typology_file = _get_default_typology_path(language)
    with resources.as_file(typology_file) as path:
        with open(path, 'r') as f:
            return yaml.safe_load(f)


def _build_realms(data: dict) -> dict[str, Realm]:
    """Build realms dictionary from raw YAML data."""
    realms = {}

    for realm_data in data.get('realms', []):
        realm_code = realm_data.get('code')

        biomes = {}
        for biome_data in realm_data.get('biomes', []):
            biome_code = biome_data.get('code')

            functional_groups = {}
            for fg_data in biome_data.get('functional_groups', []):
                fg_code = fg_data.get('code')
                functional_groups[fg_code] = FunctionalGroup(
                    code=fg_code,
                    name=fg_data.get('name', ''),
                    description=fg_data.get('description', ''),
                    url=fg_data.get('url', ''),
                    biome_code=biome_code,
                    realm_code=realm_code,
                )

            biomes[biome_code] = Biome(
                code=biome_code,
                name=biome_data.get('name', ''),
                description=biome_data.get('description', ''),
                url=biome_data.get('url', ''),
                functional_groups=functional_groups,
                realm_code=realm_code,
            )

        realms[realm_code] = Realm(
            code=realm_code,
            name=realm_data.get('name', ''),
            description=realm_data.get('description', ''),
            transitional=realm_data.get('transitional', False),
            url=realm_data.get('url', ''),
            biomes=biomes,
        )

    return realms


def get_realms(language="english") -> dict[str, Realm]:
    """
    Get all realms from the IUCN Global Ecosystem Typology.

    Realms are the highest level (Level 1) of the typology, distinguished by
    major environmental factors. GET 2.0 includes 4 core realms (T=Terrestrial,
    M=Marine, F=Freshwater, S=Subterranean) and 6 transitional realms.

    Args:
        language: Language for typology data (default: "english").

    Returns:
        dict: Dictionary with realm codes as keys and Realm instances as values.

    Example:
        >>> realms = get_realms()
        >>> realms['T'].name
        'Terrestrial'
    """
    return Typology(language=language).realms


def get_biomes(realm: str = None, language="english") -> dict[str, Biome]:
    """
    Get biomes from the IUCN Global Ecosystem Typology.

    Biomes are Level 2 of the typology, representing components of realms
    united by broad features of ecosystem structure. GET 2.0 includes 25 biomes
    across all realms.

    Args:
        realm: Optional realm code to filter biomes (e.g., 'T', 'M', 'F', 'S', 'TF', etc.)
               If None, returns all 25 biomes from all realms.
        language: Language for typology data (default: "english").

    Returns:
        dict: Dictionary with biome codes as keys and Biome instances as values.

    Raises:
        ValueError: If the specified realm code is not found.

    Examples:
        >>> all_biomes = get_biomes()           # All 25 biomes
        >>> t_biomes = get_biomes(realm='T')    # 7 Terrestrial biomes (T1-T7)
        >>> mt_biomes = get_biomes(realm='MT')  # 3 Marine-Terrestrial biomes
    """
    return Typology(language=language).get_biomes(realm)


def get_groups(realm: str = None, biome: str = None, language="english") -> dict[str, FunctionalGroup]:
    """
    Get Ecosystem Functional Groups from the IUCN Global Ecosystem Typology.

    Ecosystem Functional Groups (EFGs) are Level 3 of the typology, representing
    groups of related ecosystems within a biome that share common ecological
    drivers. GET 2.0 includes 109 EFGs across all biomes.

    Args:
        realm: Optional realm code to filter (e.g., 'T', 'M', 'F', 'S', 'TF', etc.)
               If None, searches all realms.
        biome: Optional biome code to filter (e.g., 'T1', 'M2', 'MT1', etc.)
               If None, returns all functional groups from the specified realm(s).
        language: Language for typology data (default: "english").

    Returns:
        dict: Dictionary with EFG codes as keys and FunctionalGroup instances as values.

    Raises:
        ValueError: If realm or biome code is not found.

    Examples:
        >>> all_groups = get_groups()              # All 109 EFGs
        >>> t_groups = get_groups(realm='T')       # 34 Terrestrial EFGs
        >>> t1_groups = get_groups(biome='T1')     # 4 Tropical forest EFGs
    """
    return Typology(language=language).get_groups(realm, biome)


def main():
    """Print package version."""
    print(f"iucn-get-data {version('iucn-get-data')}")


if __name__ == "__main__":
    main()
