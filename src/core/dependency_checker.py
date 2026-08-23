from typing import Dict, Any, Tuple
from src.core.version_checker import VersionChecker

class DependencyChecker:
    def __init__(self, scan_results: Dict[str, Dict[str, Any]]):
        """Initializes the dependency checker with the scan results.
        
        Args:
            scan_results (Dict[str, Dict[str, Any]]): The results dictionary from ToolDetector.scan().
        """
        self.scan_results = scan_results

    def check(self) -> Dict[str, Dict[str, Any]]:
        """Checks dependencies for all scanned tools.
        
        Returns:
            Dict[str, Dict[str, Any]]: Dictionary mapping tool ID to check results:
                {
                    "status": str ("READY", "MISSING", "OUTDATED", "OPTIONAL", "UNKNOWN", "ERROR"),
                    "message": str
                }
        """
        results = {}
        for tool_id, tool in self.scan_results.items():
            installed = tool.get("installed", False)
            required = tool.get("required", False)
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
                    "message": "Tool installed but version could not be identified"
                }
            elif not installed:
                if required:
                    results[tool_id] = {
                        "status": "MISSING",
                        "message": "Required tool is missing"
                    }
                else:
                    results[tool_id] = {
                        "status": "OPTIONAL",
                        "message": "Optional tool is not installed"
                    }
            else:
                # Installed and version exists
                if VersionChecker.is_compatible(parsed_ver, min_ver):
                    results[tool_id] = {
                        "status": "READY",
                        "message": "Installed and compatible"
                    }
                else:
                    results[tool_id] = {
                        "status": "OUTDATED",
                        "message": f"Installed version ({parsed_ver}) is older than required minimum ({min_ver})"
                    }
        return results

    def calculate_score(self, check_results: Dict[str, Dict[str, Any]]) -> Tuple[int, str]:
        """Calculates the environment score and overall readiness status.
        
        Args:
            check_results (Dict[str, Dict[str, Any]]): The results from check().
            
        Returns:
            Tuple[int, str]: (environment_score, readiness_status)
        """
        score = 100
        
        for tool_id, res in check_results.items():
            status = res["status"]
            # To get required flag, lookup from scan_results
            tool_info = self.scan_results.get(tool_id, {})
            required = tool_info.get("required", False)
            
            if status == "MISSING":
                score -= 25
            elif status == "OPTIONAL":
                score -= 5
            elif status == "OUTDATED":
                if required:
                    score -= 15
                else:
                    score -= 5  # Deduction for outdated optional tool
            elif status in ("UNKNOWN", "ERROR"):
                score -= 5

        # Enforce bounds
        score = max(0, min(100, score))
        
        # Determine readiness status
        if score >= 90:
            readiness = "READY"
        elif score >= 70:
            readiness = "MOSTLY READY"
        else:
            readiness = "NOT READY"
            
        return score, readiness