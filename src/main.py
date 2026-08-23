import argparse
import sys
import os

from src.core.environment_manager import EnvironmentManager
from src.core.logger import ActionLogger

VERSION = "2.0.0"

def print_scan_report(env_mgr: EnvironmentManager):
    """Executes environment scan and prints text-based status report for all 14 tools to stdout."""
    print("Executing 5-tier discovery pipeline... please wait.\n")
    scan_results = env_mgr.scan_environment()
    dep_results = env_mgr.dependency_results
    summary = env_mgr.get_status_summary()
    
    print("="*95)
    print(f" eSim Environment Manager (ESEM) v{VERSION} - Environment Scan & Discovery Report")
    print("="*95)
    print(f"Platform:          {sys.platform}")
    print(f"Environment Score: {summary['score']} / 100")
    print(f"Readiness Status:  {summary['readiness']}")
    print(f"Tools Installed:   {summary['installed_count']} / {summary['total_count']}")
    print("-"*95)
    
    # Header
    print(f"{'Tool':<18} | {'Category':<15} | {'Source':<18} | {'Version':<18} | {'Status':<10}")
    print("-"*95)
    
    for tool_id, tool in scan_results.items():
        dep_res = dep_results.get(tool_id, {})
        cat_str = env_mgr.tools_config.get(tool_id, {}).get("category", "Unknown")
        src_str = tool.get("source", "NOT_FOUND")
        ver_str = tool.get("parsed_version") or tool.get("raw_version") or "-"
        if len(ver_str) > 18:
            ver_str = ver_str[:15] + "..."
        status_str = dep_res.get("status", "UNKNOWN")
        
        print(f"{tool['display_name']:<18} | {cat_str:<15} | {src_str:<18} | {ver_str:<18} | {status_str:<10}")
        
    print("="*95)
    print("\nScore Deduction Breakdown:")
    for reason in summary["score_reasons"]:
        print(f"  [-] {reason}")
    print("\nLogs written to: logs/esim_manager.log")

def print_profiles_report(env_mgr: EnvironmentManager):
    """Prints EDA Workflow profiles evaluation."""
    env_mgr.scan_environment()
    evals = env_mgr.evaluate_profiles()

    print("="*85)
    print(f" eSim Environment Manager (ESEM) v{VERSION} - EDA Workflow Profiles Evaluation")
    print("="*85)

    for pid, peval in evals.items():
        print(f"\nProfile: [{peval['name']}] - Readiness: {peval['readiness']} ({peval['score']}%)")
        print(f"Description: {peval['description']}")
        print(f"Required Tools: {peval['required_count']} | Recommended Tools: {peval['recommended_count']}")
        print("Guidance:")
        for r in peval["reasons"]:
            print(f"  • {r}")
        print("-"*85)

def run_check(env_mgr: EnvironmentManager) -> int:
    """Executes environment check and returns exit code (0 if compatible, 1 otherwise)."""
    env_mgr.scan_environment()
    summary = env_mgr.get_status_summary()
    
    print(f"ESEM Readiness Check v{VERSION}")
    print(f"Score:  {summary['score']}/100")
    print(f"Status: {summary['readiness']}")
    
    if summary['readiness'] in ("READY", "MOSTLY READY"):
        print("Success: Host environment satisfies eSim engineering workflow requirements.")
        return 0
    else:
        print("Failure: Host environment lacks core required dependencies for eSim workflows.")
        return 1

def main():
    parser = argparse.ArgumentParser(
        description="eSim Environment Manager (ESEM) v2.0.0 - EDA Environment Intelligence Platform"
    )
    parser.add_argument(
        "--scan", action="store_true", help="Perform environment discovery scan and print 14-tool status report"
    )
    parser.add_argument(
        "--profiles", action="store_true", help="Evaluate readiness across EDA workflow profiles (eSim, Digital, PCB, VLSI)"
    )
    parser.add_argument(
        "--version", action="store_true", help="Display the ESEM version and exit"
    )
    parser.add_argument(
        "--check", action="store_true", help="Perform dependency check, display score, and exit with status code"
    )
    parser.add_argument(
        "--config", type=str, default=None, help="Path to custom tools.json configuration file"
    )

    args = parser.parse_args()

    # Initialize Logger
    ActionLogger.setup_logger()

    if args.version:
        print(f"eSim Environment Manager (ESEM) - Version {VERSION}")
        sys.exit(0)

    # Initialize Manager
    env_mgr = EnvironmentManager(args.config)

    if args.scan:
        print_scan_report(env_mgr)
        sys.exit(0)
    elif args.profiles:
        print_profiles_report(env_mgr)
        sys.exit(0)
    elif args.check:
        exit_code = run_check(env_mgr)
        sys.exit(exit_code)
    else:
        # Launch Royal Engineering Console GUI
        from src.gui.app import run
        run(args.config)

if __name__ == "__main__":
    main()