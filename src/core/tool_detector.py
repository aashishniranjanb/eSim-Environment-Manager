import shutil
import subprocess
import logging
from typing import Dict, Any

from src.utils.platform_utils import detect_platform
from src.core.version_checker import VersionChecker
from src.core.logger import ActionLogger

class ToolDetector:
    def __init__(self, tools_config: Dict[str, Dict[str, Any]]):
        """Initializes the detector with the configured tools registry.
        
        Args:
            tools_config (Dict[str, Dict[str, Any]]): Configured tools dict from ConfigManager.
        """
        self.tools = tools_config
        self.logger = ActionLogger.get_logger()

    def detect_tool(self, tool_id: str) -> Dict[str, Any]:
        """Detects a single tool by its ID.
        
        Args:
            tool_id (str): The ID of the tool in the registry.
            
        Returns:
            Dict[str, Any]: Scan result matching the output schema.
        """
        tool = self.tools[tool_id]
        display_name = tool["display_name"]
        
        # Determine platform-specific command
        current_platform = detect_platform()
        command = tool.get("command")
        if "commands" in tool and isinstance(tool["commands"], dict):
            command = tool["commands"].get(current_platform, command)
            
        version_args = tool.get("version_arguments", ["--version"])
        
        # Output schema defaults
        result = {
            "tool_id": tool_id,
            "display_name": display_name,
            "installed": False,
            "executable_path": None,
            "raw_version": None,
            "parsed_version": None,
            "status": "MISSING",
            "error": None,
            "required": tool.get("required", False),
            "minimum_version": tool.get("minimum_version", "0.0.0")
        }
        
        # Executable path discovery
        exec_path = shutil.which(command)
        if not exec_path:
            self.logger.warning(f"Tool missing: {display_name} (command '{command}' not found)")
            return result
            
        result["installed"] = True
        result["executable_path"] = exec_path
        result["status"] = "DETECTED"
        
        # Version querying
        try:
            self.logger.info(f"Checking version for {display_name} using: {command} { ' '.join(version_args) }")
            proc_res = subprocess.run(
                [command] + version_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
                shell=False
            )
            
            raw_output = (proc_res.stdout + proc_res.stderr).strip()
            result["raw_version"] = raw_output
            
            # Extract semantic version
            parsed_ver = VersionChecker.extract_version(raw_output)
            if parsed_ver:
                result["parsed_version"] = parsed_ver
                self.logger.info(f"Tool detected: {display_name} version {parsed_ver} at {exec_path}")
            else:
                result["parsed_version"] = None
                self.logger.warning(f"Could not parse version from output for {display_name}: {raw_output[:100]}")
                result["status"] = "UNKNOWN"
                
        except subprocess.TimeoutExpired as e:
            err_msg = f"Timeout expired while executing version check for {display_name}."
            self.logger.error(f"{err_msg} Error: {e}")
            result["error"] = err_msg
            result["status"] = "ERROR"
        except PermissionError as e:
            err_msg = f"Permission denied while running version command for {display_name}."
            self.logger.error(f"{err_msg} Error: {e}")
            result["error"] = err_msg
            result["status"] = "ERROR"
        except FileNotFoundError as e:
            err_msg = f"Command '{command}' not found during execution for {display_name}."
            self.logger.error(f"{err_msg} Error: {e}")
            result["error"] = err_msg
            result["status"] = "ERROR"
        except Exception as e:
            err_msg = f"Unexpected error during detection of {display_name}: {str(e)}"
            self.logger.error(err_msg)
            result["error"] = err_msg
            result["status"] = "ERROR"
            
        return result

    def scan(self) -> Dict[str, Dict[str, Any]]:
        """Scans the host system for all configured tools.
        
        Returns:
            Dict[str, Dict[str, Any]]: Map of tool IDs to scan results.
        """
        self.logger.info("Environment scan started")
        results = {}
        for tool_id in self.tools:
            results[tool_id] = self.detect_tool(tool_id)
        self.logger.info("Environment scan completed")
        return results
