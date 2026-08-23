from typing import Dict, Any, Tuple, List
from src.core.version_checker import VersionChecker

class DependencyChecker:
    def __init__(self, scan_results: Dict[str, Dict[str, Any]]):
        self.scan_results = scan_results

    def check(self) -> Dict[str, Dict[str, Any]]:
        """Checks dependencies for all scanned tools."""
        results = {}
        for tool_id, tool in self.scan_results.items():
            installed = tool.get("installed", False)
            required = tool.get("required", False)
            importance = tool.get("importance", "REQUIRED" if required else "RECOMMENDED")
            min_ver = tool.get("minimum_version", "0.0.0")
            parsed_ver = tool.get("parsed_version")
            det_status = tool.get("status", "MISSING")
            det_error = tool.get("error")

            if det_status == "ERROR":
                results[tool_id] = {
                    "status": "ERROR",
                    "message": det_error or "An error occurred during detection"
                }
            elif det_status == "UNKNOWN":
                results[tool_id] = {
                    "status": "UNKNOWN",
                    "message": "Tool installed but version could not be parsed"
                }
            elif not installed:
                if importance == "REQUIRED" or required:
                    results[tool_id] = {
                        "status": "MISSING",
                        "message": "Required core tool is missing"
                    }
                else:
                    results[tool_id] = {
                        "status": "OPTIONAL",
                        "message": f"{importance.capitalize()} tool is not installed"
                    }
            else:
                if VersionChecker.is_compatible(parsed_ver, min_ver):
                    results[tool_id] = {
                        "status": "READY",
                        "message": f"Installed and compatible ({parsed_ver} >= {min_ver})"
                    }
                else:
                    results[tool_id] = {
                        "status": "OUTDATED",
                        "message": f"Installed version ({parsed_ver}) is older than required minimum ({min_ver})"
                    }
        return results

    def calculate_score(self, check_results: Dict[str, Dict[str, Any]]) -> Tuple[int, str, List[str]]:
        """Calculates environment score, readiness status, and transparent deduction reasons.
        
        Returns:
            Tuple[int, str, List[str]]: (score, readiness, reasons_list)
        """
        # Bucket tools by importance
        core_tools = []
        rec_tools = []
        opt_tools = []

        for tool_id, tool_info in self.scan_results.items():
            importance = tool_info.get("importance", "REQUIRED" if tool_info.get("required") else "RECOMMENDED")
            if importance == "REQUIRED":
                core_tools.append(tool_id)
            elif importance == "RECOMMENDED":
                rec_tools.append(tool_id)
            else:
                opt_tools.append(tool_id)

        reasons = []

        # Category budgets (Core: 40 pts, Recommended: 30 pts, Optional: 30 pts)
        core_pts = 40.0
        core_deduct_per_missing = 40.0 / len(core_tools) if core_tools else 0.0

        rec_pts = 30.0
        rec_deduct_per_missing = 30.0 / len(rec_tools) if rec_tools else 0.0

        opt_pts = 30.0
        opt_deduct_per_missing = 30.0 / len(opt_tools) if opt_tools else 0.0

        # Evaluate Core Tools
        for tid in core_tools:
            info = self.scan_results[tid]
            status = check_results.get(tid, {}).get("status", "MISSING")
            name = info.get("display_name", tid)

            if status == "MISSING":
                core_pts -= core_deduct_per_missing
                reasons.append(f"Required core tool '{name}' is missing (-{int(core_deduct_per_missing)} pts)")
            elif status == "OUTDATED":
                core_pts -= (core_deduct_per_missing * 0.5)
                reasons.append(f"Required core tool '{name}' is outdated (-{int(core_deduct_per_missing * 0.5)} pts)")
            elif status in ("UNKNOWN", "ERROR"):
                core_pts -= (core_deduct_per_missing * 0.25)
                reasons.append(f"Core tool '{name}' status is {status} (-{int(core_deduct_per_missing * 0.25)} pts)")

        # Evaluate Recommended Tools
        for tid in rec_tools:
            info = self.scan_results[tid]
            status = check_results.get(tid, {}).get("status", "OPTIONAL")
            name = info.get("display_name", tid)

            if status in ("MISSING", "OPTIONAL"):
                rec_pts -= rec_deduct_per_missing
                reasons.append(f"Recommended tool '{name}' is not installed (-{int(rec_deduct_per_missing)} pts)")
            elif status == "OUTDATED":
                rec_pts -= (rec_deduct_per_missing * 0.5)
                reasons.append(f"Recommended tool '{name}' is outdated (-{int(rec_deduct_per_missing * 0.5)} pts)")

        # Evaluate Optional Tools
        for tid in opt_tools:
            info = self.scan_results[tid]
            status = check_results.get(tid, {}).get("status", "OPTIONAL")
            name = info.get("display_name", tid)

            if status in ("MISSING", "OPTIONAL"):
                opt_pts -= opt_deduct_per_missing
                reasons.append(f"Optional tool '{name}' is missing (-{int(opt_deduct_per_missing)} pts)")

        total_score = max(0, min(100, int(round(core_pts + rec_pts + opt_pts))))

        if total_score >= 90:
            readiness = "READY"
        elif total_score >= 70:
            readiness = "MOSTLY READY"
        else:
            readiness = "NOT READY"

        if not reasons:
            reasons.append("All core, recommended, and optional tool dependencies are fully satisfied.")

        return total_score, readiness, reasons