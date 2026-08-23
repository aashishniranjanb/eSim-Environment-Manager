from typing import Dict, Any, Optional

from src.core.config_manager import ConfigManager
from src.core.tool_detector import ToolDetector
from src.core.dependency_checker import DependencyChecker
from src.core.installer import Installer
from src.core.updater import Updater
from src.core.logger import ActionLogger

class EnvironmentManager:
    def __init__(self, config_path: str = None):
        """Initializes the Environment Manager and its dependencies.
        
        Args:
            config_path (str): Custom configuration path if any.
        """
        self.logger = ActionLogger.get_logger()
        self.config_manager = ConfigManager(config_path)
        
        try:
            self.tools_config = self.config_manager.load_config()
        except Exception as e:
            self.logger.error(f"Failed to load tools registry configuration: {e}")
            self.tools_config = {}

        self.detector = ToolDetector(self.tools_config)
        self.installer = Installer()
        self.updater = Updater()

        # Cache variables
        self.scan_results: Dict[str, Dict[str, Any]] = {}
        self.dependency_results: Dict[str, Dict[str, Any]] = {}
        self.score: int = 100
        self.readiness: str = "READY"

    def scan_environment(self) -> Dict[str, Dict[str, Any]]:
        """Scans the host system for configured tools and checks their dependencies.
        
        Returns:
            Dict[str, Dict[str, Any]]: The scan results.
        """
        self.scan_results = self.detector.scan()
        self.check_dependencies()
        return self.scan_results

    def check_dependencies(self) -> Dict[str, Dict[str, Any]]:
        """Re-evaluates compatibility and scores based on current scan results.
        
        Returns:
            Dict[str, Dict[str, Any]]: The dependency checker results.
        """
        if not self.scan_results:
            # If we haven't scanned yet, do a quick scan first
            self.scan_results = self.detector.scan()

        checker = DependencyChecker(self.scan_results)
        self.dependency_results = checker.check()
        self.score, self.readiness = checker.calculate_score(self.dependency_results)
        
        self.logger.info(f"Dependency check finished. Score: {self.score}, Readiness: {self.readiness}")
        return self.dependency_results

    def install_tool(self, tool_id: str) -> Dict[str, Any]:
        """Triggers safety checks and performs tool installation.
        
        Args:
            tool_id (str): ID of the tool to install.
            
        Returns:
            Dict[str, Any]: Result map from installation.
        """
        if tool_id not in self.tools_config:
            return {"success": False, "output": f"Tool '{tool_id}' not found in registry."}

        tool = self.tools_config[tool_id]
        res = self.installer.install(tool_id, tool)
        
        if res.get("success"):
            self.logger.success(f"Verification following install for '{tool_id}'...")
            # Rescan to verify installation
            self.scan_environment()
            
        return res

    def upgrade_tool(self, tool_id: str) -> Dict[str, Any]:
        """Triggers safety checks and performs tool upgrade.
        
        Args:
            tool_id (str): ID of the tool to upgrade.
            
        Returns:
            Dict[str, Any]: Result map from upgrade.
        """
        if tool_id not in self.tools_config:
            return {"success": False, "output": f"Tool '{tool_id}' not found in registry."}

        tool = self.tools_config[tool_id]
        res = self.updater.upgrade(tool_id, tool)
        
        if res.get("success"):
            self.logger.success(f"Verification following upgrade for '{tool_id}'...")
            # Rescan to verify upgrade
            self.scan_environment()
            
        return res

    def get_environment_score(self) -> int:
        """Returns the cached environment score."""
        return self.score

    def get_status_summary(self) -> Dict[str, Any]:
        """Returns a cached dashboard status summary."""
        installed = sum(1 for t in self.scan_results.values() if t.get("installed", False))
        missing = sum(1 for t in self.scan_results.values() if not t.get("installed", False))
        total = len(self.scan_results)

        return {
            "score": self.score,
            "readiness": self.readiness,
            "installed_count": installed,
            "missing_count": missing,
            "total_count": total
        }

