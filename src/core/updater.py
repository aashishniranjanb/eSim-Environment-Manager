import subprocess
import shutil
import logging
import re
from typing import Dict, Any, List, Optional

from src.utils.platform_utils import detect_platform
from src.core.logger import ActionLogger

class Updater:
    def __init__(self):
        self.logger = ActionLogger.get_logger()

    def is_package_manager_available(self) -> bool:
        """Checks if a package manager is available for the current platform."""
        plat = detect_platform()
        if plat == "windows":
            return shutil.which("winget") is not None
        elif plat == "linux":
            return shutil.which("apt-get") is not None
        elif plat == "macos":
            return shutil.which("brew") is not None
        return False

    def check_update_available(self, tool: Dict[str, Any]) -> Optional[bool]:
        """Checks if an update is available for the tool via the platform package manager.
        
        Returns:
            Optional[bool]: True if update is available, False if not, None if unsupported/error.
        """
        if not self.is_package_manager_available():
            return None

        plat = detect_platform()
        packages = tool.get("packages", {})
        package_name = packages.get(plat)
        
        if not package_name:
            return None

        try:
            if plat == "windows":
                # winget upgrade returns a list of packages that have updates.
                # If we filter by ID, winget upgrade --id <id> will return exit code 0 or say no updates available.
                # Specifically, "winget upgrade" lists all. Let's run "winget upgrade" and search for the package name/id.
                res = subprocess.run(
                    ["winget", "upgrade"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=15,
                    shell=False
                )
                output = res.stdout or ""
                # Search case-insensitively for the package name or ID in the output
                if package_name.lower() in output.lower():
                    return True
                return False

            elif plat == "linux":
                # apt-get --just-print install package_name
                # If it says "0 upgraded", then no update is available.
                res = subprocess.run(
                    ["apt-get", "--just-print", "install", package_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=15,
                    shell=False
                )
                output = res.stdout or ""
                # If "0 upgraded" or "is already the newest version" is in the output, then no update
                if "already the newest version" in output or "0 upgraded" in output:
                    return False
                # If there's an upgrade
                if "upgraded" in output.lower() or "newly installed" in output.lower():
                    return True
                return False

            elif plat == "macos":
                # brew outdated returns the list of outdated formulas.
                res = subprocess.run(
                    ["brew", "outdated"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=15,
                    shell=False
                )
                output = res.stdout or ""
                if package_name.lower() in output.lower().splitlines():
                    return True
                return False

        except Exception as e:
            self.logger.warning(f"Error checking update availability for {tool['display_name']}: {e}")
            return None

        return None

    def build_upgrade_command(self, tool: Dict[str, Any]) -> Optional[List[str]]:
        """Constructs the upgrade command for the given tool on the current platform.
        
        Args:
            tool (Dict[str, Any]): The tool registry definition.
            
        Returns:
            Optional[List[str]]: The command list, or None if upgrade is not supported.
        """
        plat = detect_platform()
        allowed_methods = tool.get("update_methods", [])
        packages = tool.get("packages", {})
        package_name = packages.get(plat)
        
        if not package_name:
            return None

        if plat == "windows":
            if "winget" in allowed_methods and shutil.which("winget"):
                return ["winget", "upgrade", "--id", package_name, "--exact", "--interactive"]
        elif plat == "linux":
            if "apt" in allowed_methods and shutil.which("apt-get"):
                return ["sudo", "apt-get", "install", "--only-upgrade", "-y", package_name]
        elif plat == "macos":
            if "brew" in allowed_methods and shutil.which("brew"):
                return ["brew", "upgrade", package_name]
                
        return None

    def upgrade(self, tool_id: str, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Executes the upgrade command for the tool.
        
        Args:
            tool_id (str): The ID of the tool.
            tool (Dict[str, Any]): The tool registry definition.
            
        Returns:
            Dict[str, Any]: A dictionary containing execution status and output.
        """
        cmd = self.build_upgrade_command(tool)
        if not cmd:
            self.logger.warning(f"Manual upgrade required for tool '{tool_id}'")
            return {
                "success": False,
                "output": "Manual upgrade required. No automatic upgrade commands available for this platform."
            }

        cmd_str = " ".join(cmd)
        self.logger.info(f"Upgrade started for '{tool_id}' using command: {cmd_str}")
        
        try:
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
                self.logger.success(f"Upgrade completed successfully for '{tool_id}'")
            else:
                self.logger.error(f"Upgrade failed for '{tool_id}' with exit code {res.returncode}. Output:\n{output}")
                
            return {
                "success": success,
                "output": output,
                "exit_code": res.returncode
            }
            
        except subprocess.TimeoutExpired as e:
            err_msg = f"Upgrade command timed out for '{tool_id}'"
            self.logger.error(err_msg)
            return {
                "success": False,
                "output": f"{err_msg}. Output so far:\n{(e.stdout or '') + (e.stderr or '')}"
            }
        except Exception as e:
            err_msg = f"Failed to execute upgrade command for '{tool_id}': {e}"
            self.logger.error(err_msg)
            return {
                "success": False,
                "output": str(e)
            }

