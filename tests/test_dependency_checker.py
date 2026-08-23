import pytest
from src.core.dependency_checker import DependencyChecker

def test_dependency_states():
    # 1. Required and installed tool becomes READY
    scan_results_1 = {
        "python": {
            "display_name": "Python",
            "installed": True,
            "parsed_version": "3.12.4",
            "minimum_version": "3.10.0",
            "required": True,
            "status": "DETECTED",
            "error": None
        }
    }
    checker_1 = DependencyChecker(scan_results_1)
    res_1 = checker_1.check()
    assert res_1["python"]["status"] == "READY"
    assert "compatible" in res_1["python"]["message"].lower()

    # 2. Required missing tool becomes MISSING
    scan_results_2 = {
        "python": {
            "display_name": "Python",
            "installed": False,
            "parsed_version": None,
            "minimum_version": "3.10.0",
            "required": True,
            "status": "MISSING",
            "error": None
        }
    }
    checker_2 = DependencyChecker(scan_results_2)
    res_2 = checker_2.check()
    assert res_2["python"]["status"] == "MISSING"

    # 3. Outdated tool becomes OUTDATED
    scan_results_3 = {
        "python": {
            "display_name": "Python",
            "installed": True,
            "parsed_version": "3.9.0",
            "minimum_version": "3.10.0",
            "required": True,
            "status": "DETECTED",
            "error": None
        }
    }
    checker_3 = DependencyChecker(scan_results_3)
    res_3 = checker_3.check()
    assert res_3["python"]["status"] == "OUTDATED"

    # 4. Optional missing tool becomes OPTIONAL
    scan_results_4 = {
        "kicad": {
            "display_name": "KiCad",
            "installed": False,
            "parsed_version": None,
            "minimum_version": "6.0.0",
            "required": False,
            "status": "MISSING",
            "error": None
        }
    }
    checker_4 = DependencyChecker(scan_results_4)
    res_4 = checker_4.check()
    assert res_4["kicad"]["status"] == "OPTIONAL"

def test_environment_score_calculation():
    # 5. Environment score remains 0-100
    
    # Perfect score
    scan_results = {
        "python": {"installed": True, "required": True, "minimum_version": "3.10.0", "parsed_version": "3.12.4", "status": "DETECTED"},
        "git": {"installed": True, "required": True, "minimum_version": "2.0.0", "parsed_version": "2.40.0", "status": "DETECTED"},
        "kicad": {"installed": True, "required": False, "minimum_version": "6.0.0", "parsed_version": "8.0.0", "status": "DETECTED"},
        "ngspice": {"installed": True, "required": False, "minimum_version": "30.0", "parsed_version": "38.0", "status": "DETECTED"}
    }
    checker = DependencyChecker(scan_results)
    check_res = checker.check()
    score, readiness = checker.calculate_score(check_res)
    assert score == 100
    assert readiness == "READY"

    # Required missing (-25) and Optional missing (-5) -> 70 (MOSTLY READY)
    scan_results_2 = {
        "python": {"installed": False, "required": True, "minimum_version": "3.10.0", "parsed_version": None, "status": "MISSING"},
        "git": {"installed": True, "required": True, "minimum_version": "2.0.0", "parsed_version": "2.40.0", "status": "DETECTED"},
        "kicad": {"installed": False, "required": False, "minimum_version": "6.0.0", "parsed_version": None, "status": "MISSING"},
        "ngspice": {"installed": True, "required": False, "minimum_version": "30.0", "parsed_version": "38.0", "status": "DETECTED"}
    }
    checker_2 = DependencyChecker(scan_results_2)
    check_res_2 = checker_2.check()
    score_2, readiness_2 = checker_2.calculate_score(check_res_2)
    assert score_2 == 70
    assert readiness_2 == "MOSTLY READY"

    # Outdated required (-15), Error (-5), Missing optional (-5) -> 75 (MOSTLY READY)
    scan_results_3 = {
        "python": {"installed": True, "required": True, "minimum_version": "3.10.0", "parsed_version": "3.9.0", "status": "DETECTED"},
        "git": {"installed": True, "required": True, "minimum_version": "2.0.0", "parsed_version": None, "status": "ERROR", "error": "Command failed"},
        "kicad": {"installed": False, "required": False, "minimum_version": "6.0.0", "parsed_version": None, "status": "MISSING"}
    }
    checker_3 = DependencyChecker(scan_results_3)
    check_res_3 = checker_3.check()
    score_3, readiness_3 = checker_3.calculate_score(check_res_3)
    assert score_3 == 75
    assert readiness_3 == "MOSTLY READY"

    # Extremely low score (bound to 0)
    scan_results_4 = {
        "python": {"installed": False, "required": True, "minimum_version": "3.10.0", "parsed_version": None, "status": "MISSING"},
        "git": {"installed": False, "required": True, "minimum_version": "2.0.0", "parsed_version": None, "status": "MISSING"},
        "tool3": {"installed": False, "required": True, "minimum_version": "1.0.0", "parsed_version": None, "status": "MISSING"},
        "tool4": {"installed": False, "required": True, "minimum_version": "1.0.0", "parsed_version": None, "status": "MISSING"},
        "tool5": {"installed": False, "required": True, "minimum_version": "1.0.0", "parsed_version": None, "status": "MISSING"}
    }
    checker_4 = DependencyChecker(scan_results_4)
    check_res_4 = checker_4.check()
    score_4, readiness_4 = checker_4.calculate_score(check_res_4)
    assert score_4 == 0
    assert readiness_4 == "NOT READY"

