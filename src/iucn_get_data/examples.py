"""Example usage of the iucn_get_data package."""

from .main import get_realms, get_biomes, get_groups, Typology


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

    # Example usage - Typology class
    print("\nExample: Get complete typology data")
    typology = Typology()
    print(f"Total realms in typology: {len(typology.realms)}")

    # Example: Access via class hierarchy
    print("\nExample: Access via class hierarchy")
    realm = typology.realms['T']
    biome = realm.biomes['T1']
    fg = biome.functional_groups['T1.1']
    print(f"  Realm: {realm.name}")
    print(f"  Biome: {biome.name}")
    print(f"  Functional Group: {fg.name}")

    # Example: Using Spanish language
    print("\nExample: Using Spanish language")
    typology_es = Typology(language="spanish")
    realm_es = typology_es.realms['T']
    biome_es = realm_es.biomes['T1']
    fg_es = biome_es.functional_groups['T1.1']
    print(f"  Realm: {realm_es.name}")
    print(f"  Biome: {biome_es.name}")
    print(f"  Functional Group: {fg_es.name}")


if __name__ == "__main__":
    main()
