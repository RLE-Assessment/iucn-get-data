import pytest
from iucn_get_data.core import get_realms, get_biomes, get_groups
from iucn_get_data.core import Typology, Realm, Biome, FunctionalGroup


def test_get_realms_returns_dict():
    """Test that get_realms returns a dictionary."""
    realms = get_realms()
    assert isinstance(realms, dict)


def test_get_realms_values_are_realm_instances():
    """Test that get_realms returns Realm instances."""
    realms = get_realms()
    for realm in realms.values():
        assert isinstance(realm, Realm)


def test_get_realms_count():
    """Test that get_realms returns 10 realms (4 core + 6 transitional)."""
    realms = get_realms()
    assert len(realms) == 10


def test_get_realms_structure():
    """Test that each realm has the required attributes."""
    realms = get_realms()

    for realm in realms.values():
        assert hasattr(realm, 'code')
        assert hasattr(realm, 'name')
        assert hasattr(realm, 'transitional')
        assert hasattr(realm, 'url')
        assert hasattr(realm, 'biomes')


def test_get_realms_core_realms():
    """Test that there are 4 core realms (T, M, F, S)."""
    realms = get_realms()
    core_realms = [r for r in realms.values() if not r.transitional]

    assert len(core_realms) == 4
    core_codes = {r.code for r in core_realms}
    assert core_codes == {'T', 'M', 'F', 'S'}


def test_get_realms_transitional_realms():
    """Test that there are 6 transitional realms."""
    realms = get_realms()
    transitional_realms = [r for r in realms.values() if r.transitional]

    assert len(transitional_realms) == 6
    transitional_codes = {r.code for r in transitional_realms}
    assert transitional_codes == {'TF', 'FM', 'MFT', 'MT', 'SF', 'SM'}


def test_get_realms_biomes_structure():
    """Test that each realm has biomes with proper structure."""
    realms = get_realms()

    for realm in realms.values():
        assert isinstance(realm.biomes, dict)
        assert len(realm.biomes) > 0, f"Realm {realm.code} has no biomes"

        for biome in realm.biomes.values():
            assert isinstance(biome, Biome)
            assert hasattr(biome, 'code')
            assert hasattr(biome, 'name')
            assert hasattr(biome, 'url')
            assert hasattr(biome, 'functional_groups')


def test_get_realms_functional_groups_structure():
    """Test that functional groups have proper structure."""
    realms = get_realms()

    for realm in realms.values():
        for biome in realm.biomes.values():
            assert isinstance(biome.functional_groups, dict)
            assert len(biome.functional_groups) > 0, f"Biome {biome.code} has no functional groups"

            for fg in biome.functional_groups.values():
                assert isinstance(fg, FunctionalGroup)
                assert hasattr(fg, 'code')
                assert hasattr(fg, 'name')
                assert hasattr(fg, 'url')


def test_get_realms_total_functional_groups():
    """Test that there are 109 total functional groups."""
    realms = get_realms()
    total_fgs = 0

    for realm in realms.values():
        for biome in realm.biomes.values():
            total_fgs += len(biome.functional_groups)

    assert total_fgs == 109


def test_get_realms_url_format():
    """Test that URLs follow the expected format."""
    realms = get_realms()
    base_url = "https://global-ecosystems.org/explore"

    for realm in realms.values():
        assert realm.url.startswith(f"{base_url}/realms/")

        for biome in realm.biomes.values():
            assert biome.url.startswith(f"{base_url}/biomes/")

            for fg in biome.functional_groups.values():
                assert fg.url.startswith(f"{base_url}/groups/")


def test_get_realms_specific_realm_data():
    """Test specific data for Terrestrial realm."""
    realms = get_realms()
    terrestrial = realms.get('T')

    assert terrestrial is not None
    assert terrestrial.name == 'Terrestrial'
    assert terrestrial.transitional is False
    assert len(terrestrial.biomes) == 7  # T1-T7
    assert terrestrial.url == 'https://global-ecosystems.org/explore/realms/T'


def test_get_realms_terrestrial_functional_groups():
    """Test that Terrestrial realm has 34 functional groups."""
    realms = get_realms()
    terrestrial = realms.get('T')

    total_fgs = sum(len(biome.functional_groups) for biome in terrestrial.biomes.values())
    assert total_fgs == 34


def test_get_realms_marine_m1_has_10_groups():
    """Test that Marine M1 biome has 10 functional groups (including M1.10)."""
    realms = get_realms()
    marine = realms.get('M')
    m1_biome = marine.biomes.get('M1')

    assert m1_biome is not None
    assert len(m1_biome.functional_groups) == 10

    # Check that M1.10 exists
    fg_codes = set(m1_biome.functional_groups.keys())
    assert 'M1.10' in fg_codes


def test_typology_returns_typology():
    """Test that Typology() returns a Typology instance."""
    typology = Typology()
    assert isinstance(typology, Typology)


def test_typology_has_realms():
    """Test that Typology() returns a Typology with realms dict."""
    typology = Typology()
    assert hasattr(typology, 'realms')
    assert isinstance(typology.realms, dict)


def test_typology_realms_count():
    """Test that Typology() returns 10 realms."""
    typology = Typology()
    assert len(typology.realms) == 10


def test_typology_complete_structure():
    """Test that Typology() returns complete hierarchical structure."""
    typology = Typology()

    # Verify structure exists
    assert len(typology.realms) > 0
    first_realm = next(iter(typology.realms.values()))
    assert hasattr(first_realm, 'code')
    assert hasattr(first_realm, 'name')
    assert hasattr(first_realm, 'biomes')
    assert len(first_realm.biomes) > 0

    first_biome = next(iter(first_realm.biomes.values()))
    assert hasattr(first_biome, 'functional_groups')


def test_get_biomes_returns_dict():
    """Test that get_biomes returns a dictionary."""
    biomes = get_biomes()
    assert isinstance(biomes, dict)


def test_get_biomes_values_are_biome_instances():
    """Test that get_biomes returns Biome instances."""
    biomes = get_biomes()
    for biome in biomes.values():
        assert isinstance(biome, Biome)


def test_get_biomes_filtered_by_realm():
    """Test that get_biomes can filter by realm."""
    terrestrial_biomes = get_biomes(realm='T')
    assert len(terrestrial_biomes) == 7
    for code in terrestrial_biomes.keys():
        assert code.startswith('T')


def test_get_biomes_invalid_realm():
    """Test that get_biomes raises ValueError for invalid realm."""
    with pytest.raises(ValueError):
        get_biomes(realm='INVALID')


def test_get_groups_returns_dict():
    """Test that get_groups returns a dictionary."""
    groups = get_groups()
    assert isinstance(groups, dict)


def test_get_groups_values_are_functional_group_instances():
    """Test that get_groups returns FunctionalGroup instances."""
    groups = get_groups()
    for group in groups.values():
        assert isinstance(group, FunctionalGroup)


def test_get_groups_filtered_by_realm():
    """Test that get_groups can filter by realm."""
    terrestrial_groups = get_groups(realm='T')
    assert len(terrestrial_groups) == 34
    for group in terrestrial_groups.values():
        assert group.realm_code == 'T'


def test_get_groups_filtered_by_biome():
    """Test that get_groups can filter by biome."""
    t1_groups = get_groups(biome='T1')
    assert len(t1_groups) == 4
    for group in t1_groups.values():
        assert group.biome_code == 'T1'


def test_get_groups_invalid_realm():
    """Test that get_groups raises ValueError for invalid realm."""
    with pytest.raises(ValueError):
        get_groups(realm='INVALID')


def test_get_groups_invalid_biome():
    """Test that get_groups raises ValueError for invalid biome."""
    with pytest.raises(ValueError):
        get_groups(biome='INVALID1')


def test_typology_class_navigation():
    """Test navigating the typology via class hierarchy."""
    typology = Typology()

    # Navigate to a specific functional group
    realm = typology.realms['T']
    assert realm.code == 'T'
    assert realm.name == 'Terrestrial'

    biome = realm.biomes['T1']
    assert biome.code == 'T1'
    assert biome.realm_code == 'T'

    fg = biome.functional_groups['T1.1']
    assert fg.code == 'T1.1'
    assert fg.biome_code == 'T1'
    assert fg.realm_code == 'T'


def test_typology_get_biomes_method():
    """Test the Typology.get_biomes() method."""
    typology = Typology()

    # Get all biomes
    all_biomes = typology.get_biomes()
    assert len(all_biomes) > 0

    # Get biomes for a specific realm
    t_biomes = typology.get_biomes(realm='T')
    assert len(t_biomes) == 7


def test_typology_get_groups_method():
    """Test the Typology.get_groups() method."""
    typology = Typology()

    # Get all groups
    all_groups = typology.get_groups()
    assert len(all_groups) == 109

    # Get groups for a specific realm
    t_groups = typology.get_groups(realm='T')
    assert len(t_groups) == 34

    # Get groups for a specific biome
    t1_groups = typology.get_groups(biome='T1')
    assert len(t1_groups) == 4
