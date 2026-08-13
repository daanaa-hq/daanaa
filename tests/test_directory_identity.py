from scripts.continuous_discovery.directory_identity import (
    DirectoryIdentity,
    is_exact_address_match,
    normalize_address,
)


def test_normalize_address_expands_common_abbreviations():
    assert normalize_address("2268 N.C. Hwy 5, Ste. 4") == "2268 NC HIGHWAY 5 SUITE 4"


def test_exact_address_match_accepts_zip_plus_four_and_abbreviations():
    irs = DirectoryIdentity("NC", "Aberdeen", "28315-8647", "2268 NC Highway 5")
    directory = DirectoryIdentity("NC", "Aberdeen", "28315", "2268 N.C. Hwy. 5")
    assert is_exact_address_match(irs, directory)


def test_exact_address_match_rejects_missing_or_different_street():
    irs = DirectoryIdentity("NC", "Aberdeen", "28315", "2268 NC Highway 5")
    directory = DirectoryIdentity("NC", "Aberdeen", "28315", "2270 NC Highway 5")
    assert is_exact_address_match(irs, directory)
