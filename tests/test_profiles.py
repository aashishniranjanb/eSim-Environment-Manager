import pytest
from src.core.profile_analyzer import ProfileAnalyzer

def test_profile_esim_basic_evaluation():
    profiles_config = {
        "eSim_basic": {
            "name": "eSim Core Workflow",
            "description": "Standard environment required for eSim.",
            "required": ["python", "git"],
            "recommended": ["kicad", "ngspice"]
        }
    }
    
    scan_results = {
        "python": {"display_name": "Python", "installed": True},
        "git": {"display_name": "Git", "installed": True},
        "kicad": {"display_name": "KiCad", "installed": True},
        "ngspice": {"display_name": "Ngspice", "installed": True}
    }
    
    dep_results = {
        "python": {"status": "READY"},
        "git": {"status": "READY"},
        "kicad": {"status": "READY"},
        "ngspice": {"status": "READY"}
    }
    
    analyzer = ProfileAnalyzer(profiles_config, scan_results, dep_results)
    eval_res = analyzer.evaluate_profile("eSim_basic")
    
    assert eval_res["readiness"] == "READY"
    assert eval_res["score"] == 100
    assert eval_res["required_count"] == "2/2"
    assert eval_res["recommended_count"] == "2/2"

def test_profile_digital_design_evaluation():
    profiles_config = {
        "digital_design": {
            "name": "Digital Design & RTL",
            "description": "HDL synthesis and simulation.",
            "required": ["yosys"],
            "recommended": ["iverilog", "verilator"]
        }
    }
    
    scan_results = {
        "yosys": {"display_name": "Yosys", "installed": False},
        "iverilog": {"display_name": "Icarus Verilog", "installed": False},
        "verilator": {"display_name": "Verilator", "installed": False}
    }
    
    dep_results = {
        "yosys": {"status": "MISSING"},
        "iverilog": {"status": "OPTIONAL"},
        "verilator": {"status": "OPTIONAL"}
    }
    
    analyzer = ProfileAnalyzer(profiles_config, scan_results, dep_results)
    eval_res = analyzer.evaluate_profile("digital_design")
    
    assert eval_res["readiness"] == "NOT READY"
    assert eval_res["score"] == 0
    assert "Required tool 'Yosys' is missing." in eval_res["reasons"]

def test_profile_pcb_design_evaluation():
    profiles_config = {
        "pcb_design": {
            "name": "PCB Design",
            "required": ["kicad"],
            "recommended": ["python"]
        }
    }
    
    scan_results = {
        "kicad": {"display_name": "KiCad", "installed": True},
        "python": {"display_name": "Python", "installed": True}
    }
    
    dep_results = {
        "kicad": {"status": "READY"},
        "python": {"status": "READY"}
    }
    
    analyzer = ProfileAnalyzer(profiles_config, scan_results, dep_results)
    eval_res = analyzer.evaluate_profile("pcb_design")
    
    assert eval_res["readiness"] == "READY"
    assert eval_res["score"] == 100

def test_profile_all_evaluations():
    profiles_config = {
        "p1": {"name": "P1", "required": ["python"], "recommended": []},
        "p2": {"name": "P2", "required": ["git"], "recommended": []}
    }
    scan = {"python": {}, "git": {}}
    dep = {"python": {"status": "READY"}, "git": {"status": "READY"}}
    
    analyzer = ProfileAnalyzer(profiles_config, scan, dep)
    evals = analyzer.evaluate_all()
    
    assert "p1" in evals
    assert "p2" in evals

