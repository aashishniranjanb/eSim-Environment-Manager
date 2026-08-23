from typing import Dict, Any, List, Tuple

class ProfileAnalyzer:
    def __init__(self, profiles_config: Dict[str, Dict[str, Any]], scan_results: Dict[str, Dict[str, Any]], dep_results: Dict[str, Dict[str, Any]]):
        self.profiles = profiles_config
        self.scan_results = scan_results
        self.dep_results = dep_results

    def evaluate_profile(self, profile_id: str) -> Dict[str, Any]:
        """Evaluates readiness for a specific engineering workflow profile."""
        if profile_id not in self.profiles:
            raise KeyError(f"Profile '{profile_id}' not defined in tools configuration.")

        profile = self.profiles[profile_id]
        name = profile.get("name", profile_id)
        description = profile.get("description", "")
        required_tools = profile.get("required", [])
        recommended_tools = profile.get("recommended", [])

        tools_status = {}
        reasons = []
        
        req_installed = 0
        req_total = len(required_tools)
        rec_installed = 0
        rec_total = len(recommended_tools)

        # Check required tools
        for tool_id in required_tools:
            tool_scan = self.scan_results.get(tool_id, {})
            tool_dep = self.dep_results.get(tool_id, {})
            status = tool_dep.get("status", "MISSING")
            disp_name = tool_scan.get("display_name", tool_id.capitalize())

            tools_status[tool_id] = status
            if status == "READY":
                req_installed += 1
            elif status == "OUTDATED":
                reasons.append(f"Required tool '{disp_name}' is outdated ({tool_dep.get('message', '')}).")
            else:
                reasons.append(f"Required tool '{disp_name}' is missing.")

        # Check recommended tools
        for tool_id in recommended_tools:
            tool_scan = self.scan_results.get(tool_id, {})
            tool_dep = self.dep_results.get(tool_id, {})
            status = tool_dep.get("status", "OPTIONAL")
            disp_name = tool_scan.get("display_name", tool_id.capitalize())

            tools_status[tool_id] = status
            if status == "READY":
                rec_installed += 1
            elif status == "OUTDATED":
                reasons.append(f"Recommended tool '{disp_name}' is outdated.")
            else:
                reasons.append(f"Recommended tool '{disp_name}' is not installed.")

        # Calculate percentage readiness
        # Required tools count for 70% of profile score, recommended for 30%
        req_score = (req_installed / req_total * 70) if req_total > 0 else 70
        rec_score = (rec_installed / rec_total * 30) if rec_total > 0 else 30
        score = int(round(req_score + rec_score))
        score = max(0, min(100, score))

        if req_total > 0 and req_installed < req_total:
            readiness = "NOT READY"
        elif score >= 90:
            readiness = "READY"
        elif score >= 70:
            readiness = "MOSTLY READY"
        else:
            readiness = "NOT READY"

        if not reasons:
            reasons.append("All workflow tool dependencies are satisfied and up-to-date.")

        return {
            "profile_id": profile_id,
            "name": name,
            "description": description,
            "readiness": readiness,
            "score": score,
            "required_count": f"{req_installed}/{req_total}",
            "recommended_count": f"{rec_installed}/{rec_total}",
            "tools_status": tools_status,
            "reasons": reasons
        }

    def evaluate_all(self) -> Dict[str, Dict[str, Any]]:
        """Evaluates readiness across all registered profiles."""
        evaluations = {}
        for profile_id in self.profiles:
            evaluations[profile_id] = self.evaluate_profile(profile_id)
        return evaluations

