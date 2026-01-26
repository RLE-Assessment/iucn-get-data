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


def main():
    print("Hello from iucn-get-data!")

    # Example usage
    realms = get_realms()
    print(f"\nLoaded {len(realms)} realms:")
    for realm in realms:
        realm_type = "Transitional" if realm.get('transitional', False) else "Core"
        num_biomes = len(realm.get('biomes', []))
        print(f"  - {realm['code']}: {realm['name']} ({realm_type}) - {num_biomes} biome(s)")


if __name__ == "__main__":
    main()
