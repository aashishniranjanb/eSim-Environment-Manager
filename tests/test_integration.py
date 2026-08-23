import pytest
from src.core.environment_manager import EnvironmentManager

def test_real_machine_scan_integration():
    """Performs a real integration scan against the host system."""
    env_mgr = EnvironmentManager()
    
    # 1. Execute scan
    results = env_mgr.scan_environment()
    
    # Verify all 14 tools are present in scan results
    assert len(results) >= 14
    assert "python" in results
    assert "git" in results
    assert "kicad" in results
    assert "ngspice" in results
    
    # Verify Python is found on host
    python_res = results["python"]
    assert python_res["found"] is True
    assert python_res["installed"] is True
    assert python_res["executable_path"] is not None
    assert python_res["parsed_version"] is not None

    # Verify score calculation and readiness string
    score = env_mgr.get_environment_score()
    summary = env_mgr.get_status_summary()
    assert 0 <= score <= 100
    assert summary["readiness"] in ("READY", "MOSTLY READY", "NOT READY")
    assert len(summary["score_reasons"]) > 0

    # Verify profile evaluation
    evals = env_mgr.evaluate_profiles()
    assert "eSim_basic" in evals
    assert "digital_design" in evals
    assert "pcb_design" in evals
    assert "open_source_vlsi" in evals

