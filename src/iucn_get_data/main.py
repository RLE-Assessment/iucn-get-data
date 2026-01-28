import yaml
from pathlib import Path
from importlib import resources


def _get_default_typology_path():
    """Get the path to the bundled typology.yaml file."""
    return resources.files("iucn_get_data").joinpath("data/typology.yaml")


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


def get_realms(file_path=None):
    """
    Get realms from the YAML file as a dictionary.

    Args:
        file_path: Path to a custom typology YAML file. If None, uses the bundled data file.

    Returns:
        dict: Dictionary with realm codes as keys and realm data as values
    """
    data = _load_yaml(file_path)
    realms_list = data.get('realms', [])
    return {r.get('code'): r for r in realms_list}


def get_biomes(realm=None, file_path=None):
    """
    Get biomes from the YAML file as a dictionary, optionally filtered by realm.

    Args:
        realm: Optional realm code to filter biomes (e.g., 'T', 'M', 'F', 'S', 'TF', etc.)
               If None, returns all biomes from all realms.
        file_path: Path to a custom typology YAML file. If None, uses the bundled data file.

    Returns:
        dict: Dictionary with biome codes as keys and biome data as values

    Examples:
        >>> # Get all biomes
        >>> all_biomes = get_biomes()
        >>> # Get only Terrestrial biomes
        >>> terrestrial_biomes = get_biomes(realm='T')
        >>> # Get only Marine-Terrestrial transitional biomes
        >>> mt_biomes = get_biomes(realm='MT')
    """
    realms = get_realms(file_path)

    all_biomes = {}

    if realm is None:
        # Return all biomes from all realms
        for realm_code, r in realms.items():
            for b in r.get('biomes', []):
                biome_with_context = {**b, 'realm_code': realm_code}
                all_biomes[b.get('code')] = biome_with_context
        return all_biomes

    # Filter by specific realm
    if realm in realms:
        r = realms[realm]
        for b in r.get('biomes', []):
            biome_with_context = {**b, 'realm_code': realm}
            all_biomes[b.get('code')] = biome_with_context
        return all_biomes

    # Realm not found
    raise ValueError(f"Realm '{realm}' not found. Valid realms: {', '.join(realms.keys())}")


def get_groups(realm=None, biome=None, file_path=None):
    """
    Get functional groups from the YAML file as a dictionary, optionally filtered by realm and/or biome.

    Args:
        realm: Optional realm code to filter functional groups (e.g., 'T', 'M', 'F', 'S', 'TF', etc.)
               If None, searches all realms.
        biome: Optional biome code to filter functional groups (e.g., 'T1', 'M2', 'MT1', etc.)
               If None, returns all functional groups from the specified realm(s).
        file_path: Path to a custom typology YAML file. If None, uses the bundled data file.

    Returns:
        dict: Dictionary with functional group codes as keys and group data as values

    Raises:
        ValueError: If realm or biome code is not found

    Examples:
        >>> # Get all functional groups
        >>> all_groups = get_groups()
        >>> # Get all functional groups from Terrestrial realm
        >>> terrestrial_groups = get_groups(realm='T')
        >>> # Get functional groups from a specific biome
        >>> t1_groups = get_groups(biome='T1')
        >>> # Get functional groups from a biome in a specific realm
        >>> t1_groups = get_groups(realm='T', biome='T1')
    """
    realms = get_realms(file_path)

    # If biome is specified, extract realm from biome code if not provided
    if biome is not None and realm is None:
        # Extract realm code from biome code (e.g., 'T1' -> 'T', 'MT1' -> 'MT')
        import re
        match = re.match(r'^([A-Z]+)(\d+)$', biome)
        if match:
            realm = match.group(1)
        else:
            raise ValueError(f"Invalid biome code format: '{biome}'")

    # Filter realms if specified
    if realm is not None:
        if realm not in realms:
            raise ValueError(f"Realm '{realm}' not found. Valid realms: {', '.join(realms.keys())}")
        realms = {realm: realms[realm]}

    # Collect functional groups
    all_groups = {}

    for realm_code, r in realms.items():
        for b in r.get('biomes', []):
            # Filter by biome if specified
            if biome is not None and b.get('code') != biome:
                continue

            for group in b.get('functional_groups', []):
                group_with_context = {
                    **group,
                    'realm_code': realm_code,
                    'biome_code': b.get('code'),
                }
                all_groups[group.get('code')] = group_with_context

    # If biome was specified but no groups found, raise error
    if biome is not None and not all_groups:
        raise ValueError(f"Biome '{biome}' not found in realm '{realm}'")

    return all_groups


def get_typology(file_path=None):
    """
    Get the complete IUCN Global Ecosystem Typology data as a dictionary.

    Args:
        file_path: Path to a custom typology YAML file. If None, uses the bundled data file.

    Returns:
        dict: Complete typology data structure with 'realms' key containing
              all realms, biomes, and functional groups

    Example:
        >>> typology = get_typology()
        >>> typology.keys()
        dict_keys(['realms'])
        >>> len(typology['realms'])
        10
    """
    return _load_yaml(file_path)


def main():

    # Example usage - get_realms
    realms = get_realms()
    print(f"\nLoaded {len(realms)} realms:")
    for code, realm in realms.items():
        realm_type = "Transitional" if realm.get('transitional', False) else "Core"
        num_biomes = len(realm.get('biomes', []))
        print(f"  - {code}: {realm['name']} ({realm_type}) - {num_biomes} biome(s)")

    # Example usage - get_biomes
    print("\nExample: Get all biomes")
    all_biomes = get_biomes()
    print(f"Total biomes across all realms: {len(all_biomes)}")

    print("\nExample: Get Terrestrial biomes")
    terrestrial_biomes = get_biomes(realm='T')
    print(f"Terrestrial biomes: {len(terrestrial_biomes)}")
    for code, biome in terrestrial_biomes.items():
        print(f"  - {code}: {biome['name']}")

    print("\nExample: Get Marine-Terrestrial biomes")
    mt_biomes = get_biomes(realm='MT')
    print(f"Marine-Terrestrial biomes: {len(mt_biomes)}")
    for code, biome in mt_biomes.items():
        print(f"  - {code}: {biome['name']}")

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
        print(f"  - {code}: {group['name']}")

    print("\nExample: Get functional groups from biome M1")
    m1_groups = get_groups(biome='M1')
    print(f"M1 functional groups: {len(m1_groups)}")

    # Example usage - get_typology
    print("\nExample: Get complete typology data")
    typology = get_typology()
    print(f"Typology data keys: {list(typology.keys())}")
    print(f"Total realms in typology: {len(typology['realms'])}")


if __name__ == "__main__":
    main()
