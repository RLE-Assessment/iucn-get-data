import pytest
from pathlib import Path
from iucn_get_data.main import get_realms


def test_get_realms_returns_list():
    """Test that get_realms returns a list."""
    realms = get_realms()
    assert isinstance(realms, list)


def test_get_realms_count():
    """Test that get_realms returns 10 realms (4 core + 6 transitional)."""
    realms = get_realms()
    assert len(realms) == 10


def test_get_realms_structure():
    """Test that each realm has the required fields."""
    realms = get_realms()
    required_fields = ['code', 'name', 'transitional', 'url', 'biomes']

    for realm in realms:
        for field in required_fields:
            assert field in realm, f"Realm {realm.get('code', 'unknown')} missing field: {field}"


def test_get_realms_core_realms():
    """Test that there are 4 core realms (T, M, F, S)."""
    realms = get_realms()
    core_realms = [r for r in realms if not r.get('transitional', True)]

    assert len(core_realms) == 4
    core_codes = {r['code'] for r in core_realms}
    assert core_codes == {'T', 'M', 'F', 'S'}


def test_get_realms_transitional_realms():
    """Test that there are 6 transitional realms."""
    realms = get_realms()
    transitional_realms = [r for r in realms if r.get('transitional', False)]

    assert len(transitional_realms) == 6
    transitional_codes = {r['code'] for r in transitional_realms}
    assert transitional_codes == {'TF', 'FM', 'MFT', 'MT', 'SF', 'SM'}


def test_get_realms_biomes_structure():
    """Test that each realm has biomes with proper structure."""
    realms = get_realms()

    for realm in realms:
        biomes = realm.get('biomes', [])
        assert isinstance(biomes, list)
        assert len(biomes) > 0, f"Realm {realm['code']} has no biomes"

        for biome in biomes:
            assert 'code' in biome
            assert 'name' in biome
            assert 'url' in biome
            assert 'functional_groups' in biome


def test_get_realms_functional_groups_structure():
    """Test that functional groups have proper structure."""
    realms = get_realms()

    for realm in realms:
        for biome in realm.get('biomes', []):
            functional_groups = biome.get('functional_groups', [])
            assert isinstance(functional_groups, list)
            assert len(functional_groups) > 0, f"Biome {biome['code']} has no functional groups"

            for fg in functional_groups:
                assert 'code' in fg
                assert 'name' in fg
                assert 'url' in fg


def test_get_realms_total_functional_groups():
    """Test that there are 109 total functional groups."""
    realms = get_realms()
    total_fgs = 0

    for realm in realms:
        for biome in realm.get('biomes', []):
            total_fgs += len(biome.get('functional_groups', []))

    assert total_fgs == 109


def test_get_realms_url_format():
    """Test that URLs follow the expected format."""
    realms = get_realms()
    base_url = "https://global-ecosystems.org/explore"

    for realm in realms:
        assert realm['url'].startswith(f"{base_url}/realms/")

        for biome in realm.get('biomes', []):
            assert biome['url'].startswith(f"{base_url}/biomes/")

            for fg in biome.get('functional_groups', []):
                assert fg['url'].startswith(f"{base_url}/groups/")


def test_get_realms_file_not_found():
    """Test that FileNotFoundError is raised for non-existent file."""
    with pytest.raises(FileNotFoundError):
        get_realms("nonexistent/path/to/file.yaml")


def test_get_realms_specific_realm_data():
    """Test specific data for Terrestrial realm."""
    realms = get_realms()
    terrestrial = next((r for r in realms if r['code'] == 'T'), None)

    assert terrestrial is not None
    assert terrestrial['name'] == 'Terrestrial'
    assert terrestrial['transitional'] is False
    assert len(terrestrial['biomes']) == 7  # T1-T7
    assert terrestrial['url'] == 'https://global-ecosystems.org/explore/realms/T'


def test_get_realms_terrestrial_functional_groups():
    """Test that Terrestrial realm has 34 functional groups."""
    realms = get_realms()
    terrestrial = next((r for r in realms if r['code'] == 'T'), None)

    total_fgs = sum(len(biome.get('functional_groups', [])) for biome in terrestrial['biomes'])
    assert total_fgs == 34


def test_get_realms_marine_m1_has_10_groups():
    """Test that Marine M1 biome has 10 functional groups (including M1.10)."""
    realms = get_realms()
    marine = next((r for r in realms if r['code'] == 'M'), None)
    m1_biome = next((b for b in marine['biomes'] if b['code'] == 'M1'), None)

    assert m1_biome is not None
    assert len(m1_biome['functional_groups']) == 10

    # Check that M1.10 exists
    fg_codes = {fg['code'] for fg in m1_biome['functional_groups']}
    assert 'M1.10' in fg_codes


def test_get_typology_returns_dict():
    """Test that get_typology returns a dictionary."""
    from iucn_get_data.main import get_typology
    typology = get_typology()
    assert isinstance(typology, dict)


def test_get_typology_has_realms_key():
    """Test that get_typology returns a dict with 'realms' key."""
    from iucn_get_data.main import get_typology
    typology = get_typology()
    assert 'realms' in typology
    assert isinstance(typology['realms'], list)


def test_get_typology_realms_count():
    """Test that get_typology returns 10 realms."""
    from iucn_get_data.main import get_typology
    typology = get_typology()
    assert len(typology['realms']) == 10


def test_get_typology_file_not_found():
    """Test that get_typology raises FileNotFoundError for non-existent file."""
    from iucn_get_data.main import get_typology
    with pytest.raises(FileNotFoundError):
        get_typology("nonexistent/path.yaml")


def test_get_typology_complete_structure():
    """Test that get_typology returns complete hierarchical structure."""
    from iucn_get_data.main import get_typology
    typology = get_typology()

    # Verify structure exists
    assert len(typology['realms']) > 0
    first_realm = typology['realms'][0]
    assert 'code' in first_realm
    assert 'name' in first_realm
    assert 'biomes' in first_realm
    assert len(first_realm['biomes']) > 0

    first_biome = first_realm['biomes'][0]
    assert 'functional_groups' in first_biome
