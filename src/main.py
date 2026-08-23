import argparse
import sys
import os

from src.core.environment_manager import EnvironmentManager
from src.core.logger import ActionLogger

VERSION = "1.0.0"

def print_scan_report(env_mgr: EnvironmentManager):
    """Executes environment scan and prints a text-based status report to stdout."""
    print("Scanning environment... please wait.")
    scan_results = env_mgr.scan_environment()
    dep_results = env_mgr.dependency_results
    summary = env_mgr.get_status_summary()
    
    print("\n" + "="*80)
    print(f" eSim Environment Manager (ESEM) - Environment Scan Report")
    print("="*80)
    print(f"Platform: {sys.platform}")
    print(f"Environment Score: {summary['score']} / 100")
    print(f"Readiness Status:  {summary['readiness']}")
    print("-"*80)
    
    # Header
    print(f"{'Tool':<15} | {'Category':<12} | {'Installed':<9} | {'Version':<20} | {'Status':<12}")
    print("-"*80)
    
    for tool_id, tool in scan_results.items():
        dep_res = dep_results.get(tool_id, {})
        installed_str = "YES" if tool["installed"] else "NO"
        ver_str = tool["parsed_version"] or tool["raw_version"] or "-"
        if len(ver_str) > 20:
            ver_str = ver_str[:17] + "..."
        status_str = dep_res.get("status", "UNKNOWN")
        
        category_str = env_mgr.tools_config.get(tool_id, {}).get("category", "Unknown")
        print(f"{tool['display_name']:<15} | {category_str:<12} | {installed_str:<9} | {ver_str:<20} | {status_str:<12}")
        
    print("="*80)
    print("Logs written to: logs/esim_manager.log")

def run_check(env_mgr: EnvironmentManager) -> int:
    """Executes environment check and returns exit code (0 if compatible, 1 otherwise)."""
    env_mgr.scan_environment()
    summary = env_mgr.get_status_summary()
    
    print(f"ESEM Readiness Check")
    print(f"Score: {summary['score']}/100")
    print(f"Status: {summary['readiness']}")
    
    if summary['readiness'] in ("READY", "MOSTLY READY"):
        print("Success: System is ready/mostly ready for eSim workflows.")
        return 0
    else:
        print("Failure: System lacks key required environment tools for eSim workflows.")
        return 1

def main():
    parser = argparse.ArgumentParser(
        description="eSim Environment Manager (ESEM) - Automated Tool & Environment Manager"
    )
    parser.add_argument(
        "--scan", action="store_true", help="Perform an environment scan and print details to stdout"
    )
    parser.add_argument(
        "--version", action="store_true", help="Display the ESEM version and exit"
    )
    parser.add_argument(
        "--check", action="store_true", help="Perform dependency check, display score, and exit with status code"
    )
    parser.add_argument(
        "--config", type=str, default=None, help="Path to a custom tools.json configuration file"
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
    elif args.check:
        exit_code = run_check(env_mgr)
        sys.exit(exit_code)
    else:
        # Launch GUI
        from src.gui.app import run
        run(args.config)

if __name__ == "__main__":
    main()