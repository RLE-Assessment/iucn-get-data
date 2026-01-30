import re
import yaml
from dataclasses import dataclass, field
from pathlib import Path
from importlib import resources


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
        realms: Dictionary of realms keyed by their code.
    """
    realms: dict[str, Realm] = field(default_factory=dict)

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


def _get_default_typology_path(language="english"):
    """Get the path to the bundled YAML file."""
    return resources.files("iucn_get_data").joinpath(f"data/{language}.yaml")


def _load_yaml(file_path=None):
    """Load YAML data from the specified path or the default bundled file."""
    if file_path is None:
        # Use bundled data file
        typology_file = _get_default_typology_path()
        with resources.as_file(typology_file) as path:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
    else:
        # Use user-specified path
        yaml_path = Path(file_path)
        if not yaml_path.exists():
            raise FileNotFoundError(f"Typology file not found: {file_path}")
        with open(yaml_path, 'r') as f:
            return yaml.safe_load(f)


def _build_typology(data: dict) -> Typology:
    """Build a Typology instance from raw YAML data."""
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

    return Typology(realms=realms)


def get_typology(file_path=None) -> Typology:
    """
    Load the IUCN Global Ecosystem Typology (GET) 2.0.

    Returns a hierarchical data structure containing all realms, biomes, and
    ecosystem functional groups from the typology. Navigate the hierarchy via
    class attributes (e.g., typology.realms['T'].biomes['T1'].functional_groups).

    Args:
        file_path: Path to a custom typology YAML file. If None, uses the bundled data file.

    Returns:
        Typology: Complete typology with 10 realms, 25 biomes, and 109 functional groups.

    Example:
        >>> typology = get_typology()
        >>> realm = typology.realms['T']  # Terrestrial
        >>> biome = realm.biomes['T1']    # Tropical-subtropical forests
        >>> fg = biome.functional_groups['T1.1']  # Lowland rainforests
    """
    data = _load_yaml(file_path)
    return _build_typology(data)


def get_realms(file_path=None) -> dict[str, Realm]:
    """
    Get all realms from the IUCN Global Ecosystem Typology.

    Realms are the highest level (Level 1) of the typology, distinguished by
    major environmental factors. GET 2.0 includes 4 core realms (T=Terrestrial,
    M=Marine, F=Freshwater, S=Subterranean) and 6 transitional realms.

    Args:
        file_path: Path to a custom typology YAML file. If None, uses the bundled data file.

    Returns:
        dict: Dictionary with realm codes as keys and Realm instances as values.

    Example:
        >>> realms = get_realms()
        >>> realms['T'].name
        'Terrestrial'
    """
    typology = get_typology(file_path)
    return typology.realms


def get_biomes(realm: str = None, file_path=None) -> dict[str, Biome]:
    """
    Get biomes from the IUCN Global Ecosystem Typology.

    Biomes are Level 2 of the typology, representing components of realms
    united by broad features of ecosystem structure. GET 2.0 includes 25 biomes
    across all realms.

    Args:
        realm: Optional realm code to filter biomes (e.g., 'T', 'M', 'F', 'S', 'TF', etc.)
               If None, returns all 25 biomes from all realms.
        file_path: Path to a custom typology YAML file. If None, uses the bundled data file.

    Returns:
        dict: Dictionary with biome codes as keys and Biome instances as values.

    Raises:
        ValueError: If the specified realm code is not found.

    Examples:
        >>> all_biomes = get_biomes()           # All 25 biomes
        >>> t_biomes = get_biomes(realm='T')    # 7 Terrestrial biomes (T1-T7)
        >>> mt_biomes = get_biomes(realm='MT')  # 3 Marine-Terrestrial biomes
    """
    typology = get_typology(file_path)
    return typology.get_biomes(realm)


def get_groups(realm: str = None, biome: str = None, file_path=None) -> dict[str, FunctionalGroup]:
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
        file_path: Path to a custom typology YAML file. If None, uses the bundled data file.

    Returns:
        dict: Dictionary with EFG codes as keys and FunctionalGroup instances as values.

    Raises:
        ValueError: If realm or biome code is not found.

    Examples:
        >>> all_groups = get_groups()              # All 109 EFGs
        >>> t_groups = get_groups(realm='T')       # 34 Terrestrial EFGs
        >>> t1_groups = get_groups(biome='T1')     # 4 Tropical forest EFGs
    """
    typology = get_typology(file_path)
    return typology.get_groups(realm, biome)


def main():
    # Example usage - get_realms
    realms = get_realms()
    print(f"\nLoaded {len(realms)} realms:")
    for code, realm in realms.items():
        realm_type = "Transitional" if realm.transitional else "Core"
        num_biomes = len(realm.biomes)
        print(f"  - {code}: {realm.name} ({realm_type}) - {num_biomes} biome(s)")

    # Example usage - get_biomes
    print("\nExample: Get all biomes")
    all_biomes = get_biomes()
    print(f"Total biomes across all realms: {len(all_biomes)}")

    print("\nExample: Get Terrestrial biomes")
    terrestrial_biomes = get_biomes(realm='T')
    print(f"Terrestrial biomes: {len(terrestrial_biomes)}")
    for code, biome in terrestrial_biomes.items():
        print(f"  - {code}: {biome.name}")

    print("\nExample: Get Marine-Terrestrial biomes")
    mt_biomes = get_biomes(realm='MT')
    print(f"Marine-Terrestrial biomes: {len(mt_biomes)}")
    for code, biome in mt_biomes.items():
        print(f"  - {code}: {biome.name}")

    # Example usage - get_groups
    print("\nExample: Get all functional groups")
    all_groups = get_groups()
    print(f"Total functional groups: {len(all_groups)}")

    print("\nExample: Get all Terrestrial functional groups")
    terrestrial_groups = get_groups(realm='T')
    print(f"Terrestrial functional groups: {len(terrestrial_groups)}")

    print("\nExample: Get functional groups from biome T1")
    t1_groups = get_groups(biome='T1')
    print(f"T1 functional groups: {len(t1_groups)}")
    for code, group in t1_groups.items():
        print(f"  - {code}: {group.name}")

    print("\nExample: Get functional groups from biome M1")
    m1_groups = get_groups(biome='M1')
    print(f"M1 functional groups: {len(m1_groups)}")

    # Example usage - get_typology
    print("\nExample: Get complete typology data")
    typology = get_typology()
    print(f"Total realms in typology: {len(typology.realms)}")

    # Example: Access via class hierarchy
    print("\nExample: Access via class hierarchy")
    realm = typology.realms['T']
    biome = realm.biomes['T1']
    fg = biome.functional_groups['T1.1']
    print(f"  Realm: {realm.name}")
    print(f"  Biome: {biome.name}")
    print(f"  Functional Group: {fg.name}")


if __name__ == "__main__":
    main()
