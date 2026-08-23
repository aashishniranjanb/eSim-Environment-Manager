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
            "importance": "REQUIRED",
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
            "importance": "REQUIRED",
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
            "importance": "REQUIRED",
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
            "importance": "RECOMMENDED",
            "status": "MISSING",
            "error": None
        }
    }
    checker_4 = DependencyChecker(scan_results_4)
    res_4 = checker_4.check()
    assert res_4["kicad"]["status"] == "OPTIONAL"

def test_environment_score_calculation():
    # Perfect score
    scan_results = {
        "python": {"installed": True, "required": True, "importance": "REQUIRED", "minimum_version": "3.10.0", "parsed_version": "3.12.4", "status": "DETECTED"},
        "git": {"installed": True, "required": True, "importance": "REQUIRED", "minimum_version": "2.0.0", "parsed_version": "2.40.0", "status": "DETECTED"},
        "kicad": {"installed": True, "required": False, "importance": "RECOMMENDED", "minimum_version": "6.0.0", "parsed_version": "8.0.0", "status": "DETECTED"},
        "ngspice": {"installed": True, "required": False, "importance": "RECOMMENDED", "minimum_version": "30.0", "parsed_version": "38.0", "status": "DETECTED"}
    }
    checker = DependencyChecker(scan_results)
    check_res = checker.check()
    score, readiness, reasons = checker.calculate_score(check_res)
    assert score == 100
    assert readiness == "READY"
    assert len(reasons) > 0

    # Partial score deduction
    scan_results_2 = {
        "python": {"installed": False, "required": True, "importance": "REQUIRED", "minimum_version": "3.10.0", "parsed_version": None, "status": "MISSING"},
        "git": {"installed": True, "required": True, "importance": "REQUIRED", "minimum_version": "2.0.0", "parsed_version": "2.40.0", "status": "DETECTED"},
        "kicad": {"installed": False, "required": False, "importance": "RECOMMENDED", "minimum_version": "6.0.0", "parsed_version": None, "status": "MISSING"},
        "ngspice": {"installed": True, "required": False, "importance": "RECOMMENDED", "minimum_version": "30.0", "parsed_version": "38.0", "status": "DETECTED"}
    }
    checker_2 = DependencyChecker(scan_results_2)
    check_res_2 = checker_2.check()
    score_2, readiness_2, reasons_2 = checker_2.calculate_score(check_res_2)
    assert score_2 == 65
    assert readiness_2 == "NOT READY"
    assert any("Required core tool 'python' is missing" in r for r in reasons_2)
