import subprocess
import shutil
import logging
from typing import Dict, Any, List, Optional

from src.utils.platform_utils import detect_platform
from src.core.logger import ActionLogger

class Installer:
    def __init__(self):
        self.logger = ActionLogger.get_logger()

    def build_install_command(self, tool: Dict[str, Any]) -> Optional[List[str]]:
        """Constructs the installation command for the given tool on the current platform.
        
        Args:
            tool (Dict[str, Any]): The tool registry definition.
            
        Returns:
            Optional[List[str]]: The command list, or None if manual installation is required.
        """
        plat = detect_platform()
        
        # Check if platform is supported in install methods
        allowed_methods = tool.get("install_methods", [])
        
        packages = tool.get("packages", {})
        package_name = packages.get(plat)
        
        if not package_name:
            return None

        if plat == "windows":
            if "winget" in allowed_methods and shutil.which("winget"):
                # Use --exact to search by ID, --interactive or --silent can be set, but let's keep it standard
                return ["winget", "install", "--id", package_name, "--exact", "--interactive"]
        elif plat == "linux":
            if "apt" in allowed_methods and shutil.which("apt-get"):
                return ["sudo", "apt-get", "install", "-y", package_name]
        elif plat == "macos":
            if "brew" in allowed_methods and shutil.which("brew"):
                return ["brew", "install", package_name]
                
        return None

    def install(self, tool_id: str, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Executes the installation command for the tool.
        
        Args:
            tool_id (str): The ID of the tool.
            tool (Dict[str, Any]): The tool registry definition.
            
        Returns:
            Dict[str, Any]: A dictionary containing execution status and output.
        """
        cmd = self.build_install_command(tool)
        if not cmd:
            self.logger.warning(f"Manual installation required for tool '{tool_id}'")
            return {
                "success": False,
                "output": "Manual installation required. No automatic package manager mapping available for this platform."
            }

        cmd_str = " ".join(cmd)
        self.logger.info(f"Installation started for '{tool_id}' using command: {cmd_str}")
        
        try:
            # Execute command. Do not use shell=True unless necessary.
            # We don't use shell=True so it's safer.
            # Note: since sudo or winget might request user interaction, we run it and capture the output
            # If winget or apt-get is run, it could block if prompts are not handled.
            # However, since we pass --interactive (or apt has -y), we let it run.
            res = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=600 # 10 minute timeout
            )
            
            output = (res.stdout or "") + (res.stderr or "")
            success = res.returncode == 0
            
            if success:
                self.logger.success(f"Installation completed successfully for '{tool_id}'")
            else:
                self.logger.error(f"Installation failed for '{tool_id}' with exit code {res.returncode}. Output:\n{output}")
                
            return {
                "success": success,
                "output": output,
                "exit_code": res.returncode
            }
            
        except subprocess.TimeoutExpired as e:
            err_msg = f"Installation command timed out for '{tool_id}'"
            self.logger.error(err_msg)
            return {
                "success": False,
                "output": f"{err_msg}. Output so far:\n{(e.stdout or '') + (e.stderr or '')}"
            }
        except Exception as e:
            err_msg = f"Failed to execute installation command for '{tool_id}': {e}"
            self.logger.error(err_msg)
            return {
                "success": False,
                "output": str(e)
            }

    def validate_installation(self, tool: Dict[str, Any]) -> bool:
        """Checks if a tool is present on the system after installation.
        
        Args:
            tool (Dict[str, Any]): The tool registry definition.
            
        Returns:
            bool: True if command is found, False otherwise.
        """
        plat = detect_platform()
        command = tool.get("command")
        if "commands" in tool and isinstance(tool["commands"], dict):
            command = tool["commands"].get(plat, command)
        return shutil.which(command) is not None

