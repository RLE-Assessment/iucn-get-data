import yaml
from pathlib import Path


def get_realms(file_path="data/typology.yaml"):
    """
    Get a list of realms from the YAML file.

    Args:
        file_path: Path to the typology YAML file (default: "data/typology.yaml")

    Returns:
        list: List of realm dictionaries containing code, name, transitional flag, url, and biomes
    """
    yaml_path = Path(file_path)

    if not yaml_path.exists():
        raise FileNotFoundError(f"Typology file not found: {file_path}")

    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    return data.get('realms', [])


def get_biomes(realm=None, file_path="data/typology.yaml"):
    """
    Get a list of biomes from the YAML file, optionally filtered by realm.

    Args:
        realm: Optional realm code to filter biomes (e.g., 'T', 'M', 'F', 'S', 'TF', etc.)
               If None, returns all biomes from all realms.
        file_path: Path to the typology YAML file (default: "data/typology.yaml")

    Returns:
        list: List of biome dictionaries containing code, name, url, and functional_groups

    Examples:
        >>> # Get all biomes
        >>> all_biomes = get_biomes()
        >>> # Get only Terrestrial biomes
        >>> terrestrial_biomes = get_biomes(realm='T')
        >>> # Get only Marine-Terrestrial transitional biomes
        >>> mt_biomes = get_biomes(realm='MT')
    """
    realms = get_realms(file_path)

    if realm is None:
        # Return all biomes from all realms
        all_biomes = []
        for r in realms:
            all_biomes.extend(r.get('biomes', []))
        return all_biomes

    # Filter by specific realm
    for r in realms:
        if r.get('code') == realm:
            return r.get('biomes', [])

    # Realm not found
    raise ValueError(f"Realm '{realm}' not found. Valid realms: {', '.join([r.get('code') for r in realms])}")


def get_groups(realm=None, biome=None, file_path="data/typology.yaml"):
    """
    Get a list of functional groups from the YAML file, optionally filtered by realm and/or biome.

    Args:
        realm: Optional realm code to filter functional groups (e.g., 'T', 'M', 'F', 'S', 'TF', etc.)
               If None, searches all realms.
        biome: Optional biome code to filter functional groups (e.g., 'T1', 'M2', 'MT1', etc.)
               If None, returns all functional groups from the specified realm(s).
        file_path: Path to the typology YAML file (default: "data/typology.yaml")

    Returns:
        list: List of functional group dictionaries containing code, name, and url

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
        realms = [r for r in realms if r.get('code') == realm]
        if not realms:
            all_realm_codes = [r.get('code') for r in get_realms(file_path)]
            raise ValueError(f"Realm '{realm}' not found. Valid realms: {', '.join(all_realm_codes)}")

    # Collect functional groups
    all_groups = []

    for r in realms:
        for b in r.get('biomes', []):
            # Filter by biome if specified
            if biome is not None and b.get('code') != biome:
                continue

            all_groups.extend(b.get('functional_groups', []))

    # If biome was specified but no groups found, raise error
    if biome is not None and not all_groups:
        raise ValueError(f"Biome '{biome}' not found in realm '{realm}'")

    return all_groups


def get_typology(file_path="data/typology.yaml"):
    """
    Get the complete IUCN Global Ecosystem Typology data as a dictionary.

    Args:
        file_path: Path to the typology YAML file (default: "data/typology.yaml")

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
    yaml_path = Path(file_path)

    if not yaml_path.exists():
        raise FileNotFoundError(f"Typology file not found: {file_path}")

    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    return data


def main():

    # Example usage - get_realms
    realms = get_realms()
    print(f"\nLoaded {len(realms)} realms:")
    for realm in realms:
        realm_type = "Transitional" if realm.get('transitional', False) else "Core"
        num_biomes = len(realm.get('biomes', []))
        print(f"  - {realm['code']}: {realm['name']} ({realm_type}) - {num_biomes} biome(s)")

    # Example usage - get_biomes
    print("\nExample: Get all biomes")
    all_biomes = get_biomes()
    print(f"Total biomes across all realms: {len(all_biomes)}")

    print("\nExample: Get Terrestrial biomes")
    terrestrial_biomes = get_biomes(realm='T')
    print(f"Terrestrial biomes: {len(terrestrial_biomes)}")
    for biome in terrestrial_biomes:
        print(f"  - {biome['code']}: {biome['name']}")

    print("\nExample: Get Marine-Terrestrial biomes")
    mt_biomes = get_biomes(realm='MT')
    print(f"Marine-Terrestrial biomes: {len(mt_biomes)}")
    for biome in mt_biomes:
        print(f"  - {biome['code']}: {biome['name']}")

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
    for group in t1_groups:
        print(f"  - {group['code']}: {group['name']}")

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
