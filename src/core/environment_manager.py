from typing import Dict, Any, List, Optional

from src.core.config_manager import ConfigManager
from src.core.tool_discovery import ToolDiscovery
from src.core.dependency_checker import DependencyChecker
from src.core.profile_analyzer import ProfileAnalyzer
from src.core.installer import Installer
from src.core.updater import Updater
from src.core.logger import ActionLogger

class EnvironmentManager:
    def __init__(self, config_path: str = None):
        self.logger = ActionLogger.get_logger()
        self.config_manager = ConfigManager(config_path)
        
        try:
            self.tools_config = self.config_manager.load_config()
            self.profiles_config = self.config_manager.get_profiles()
        except Exception as e:
            self.logger.error(f"Failed to load tools registry configuration: {e}")
            self.tools_config = {}
            self.profiles_config = {}

        self.discovery = ToolDiscovery(self.tools_config)
        self.installer = Installer()
        self.updater = Updater()

        # Cache variables
        self.scan_results: Dict[str, Dict[str, Any]] = {}
        self.dependency_results: Dict[str, Dict[str, Any]] = {}
        self.profile_evaluations: Dict[str, Dict[str, Any]] = {}
        self.score: int = 100
        self.readiness: str = "READY"
        self.score_reasons: List[str] = []

    def scan_environment(self) -> Dict[str, Dict[str, Any]]:
        """Scans host machine for all tools using 5-tier discovery pipeline."""
        self.scan_results = self.discovery.discover_all(self.tools_config)
        self.check_dependencies()
        self.evaluate_profiles()
        return self.scan_results

    def check_dependencies(self) -> Dict[str, Dict[str, Any]]:
        """Evaluates compatibility, calculates score, and generates deduction reasons."""
        if not self.scan_results:
            self.scan_results = self.discovery.discover_all(self.tools_config)

        checker = DependencyChecker(self.scan_results)
        self.dependency_results = checker.check()
        self.score, self.readiness, self.score_reasons = checker.calculate_score(self.dependency_results)
        
        self.logger.info(f"Dependency evaluation complete. Score: {self.score}, Readiness: {self.readiness}")
        return self.dependency_results

    def evaluate_profiles(self) -> Dict[str, Dict[str, Any]]:
        """Evaluates readiness across all registered EDA workflow profiles."""
        if not self.scan_results or not self.dependency_results:
            self.scan_environment()

        analyzer = ProfileAnalyzer(self.profiles_config, self.scan_results, self.dependency_results)
        self.profile_evaluations = analyzer.evaluate_all()
        return self.profile_evaluations

    def install_tool(self, tool_id: str) -> Dict[str, Any]:
        """Triggers user-confirmed tool installation."""
        if tool_id not in self.tools_config:
            return {"success": False, "output": f"Tool '{tool_id}' not found in registry."}

        tool = self.tools_config[tool_id]
        res = self.installer.install(tool_id, tool)
        
        if res.get("success"):
            self.logger.success(f"Verification following install for '{tool_id}'...")
            self.scan_environment()
            
        return res

    def upgrade_tool(self, tool_id: str) -> Dict[str, Any]:
        """Triggers user-confirmed tool upgrade."""
        if tool_id not in self.tools_config:
            return {"success": False, "output": f"Tool '{tool_id}' not found in registry."}

        tool = self.tools_config[tool_id]
        res = self.updater.upgrade(tool_id, tool)
        
        if res.get("success"):
            self.logger.success(f"Verification following upgrade for '{tool_id}'...")
            self.scan_environment()
            
        return res

    def get_environment_score(self) -> int:
        """Returns current cached score."""
        return self.score

    def get_score_reasons(self) -> List[str]:
        """Returns score deduction explanations."""
        return self.score_reasons

    def get_status_summary(self) -> Dict[str, Any]:
        """Returns cached dashboard status summary."""
        installed = sum(1 for t in self.scan_results.values() if t.get("installed", False))
        missing = sum(1 for t in self.scan_results.values() if not t.get("installed", False))
        total = len(self.scan_results)

        return {
            "score": self.score,
            "readiness": self.readiness,
            "installed_count": installed,
            "missing_count": missing,
            "total_count": total,
            "score_reasons": self.score_reasons
        }
