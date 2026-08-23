import pytest
from src.core.version_checker import VersionChecker

def test_extract_version():
    # extract normal version
    assert VersionChecker.extract_version("Python 3.12.4") == "3.12.4"
    assert VersionChecker.extract_version("git version 2.45.2.windows.1") == "2.45.2"
    assert VersionChecker.extract_version("kicad-cli version 8.0.2") == "8.0.2"
    
    # extract version from single-number or complex command output
    assert VersionChecker.extract_version("ngspice-30 done") == "30"
    assert VersionChecker.extract_version("some output with no numbers") is None
    assert VersionChecker.extract_version("") is None
    assert VersionChecker.extract_version(None) is None

def test_compare_versions():
    # compare equal versions
    assert VersionChecker.compare_versions("3.12.4", "3.12.4") == 0
    assert VersionChecker.compare_versions("9", "9.0.0") == 0
    
    # compare newer version
    assert VersionChecker.compare_versions("3.12.4", "3.10.0") == 1
    assert VersionChecker.compare_versions("10.0", "9.2.5") == 1
    assert VersionChecker.compare_versions("3.12.4", "3.12") == 1
    
    # compare older version
    assert VersionChecker.compare_versions("3.9.0", "3.10.0") == -1
    assert VersionChecker.compare_versions("8.9.9", "9.0") == -1
    
    # invalid version comparisons
    with pytest.raises(ValueError):
        VersionChecker.compare_versions("abc", "1.0.0")
    with pytest.raises(ValueError):
        VersionChecker.compare_versions("1.0.0", "")

def test_is_compatible():
    # is_compatible checks
    assert VersionChecker.is_compatible("3.12.4", "3.10.0") is True
    assert VersionChecker.is_compatible("3.9.0", "3.10.0") is False
    assert VersionChecker.is_compatible(None, "1.0.0") is False
    assert VersionChecker.is_compatible("1.0.0", None) is False
    assert VersionChecker.is_compatible("abc", "1.0.0") is False

