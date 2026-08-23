import os
import glob
import shutil
import subprocess
from typing import Dict, Any, List, Optional, Tuple

from src.utils.platform_utils import detect_platform
from src.core.version_checker import VersionChecker
from src.core.logger import ActionLogger

class ToolDiscovery:
    def __init__(self, tools_config: Dict[str, Dict[str, Any]] = None):
        self.tools = tools_config or {}
        self.logger = ActionLogger.get_logger()

    @staticmethod
    def expand_path_patterns(patterns: List[str]) -> List[str]:
        """Expands environment variables and glob wildcards in path patterns."""
        expanded = []
        for pattern in patterns:
            exp_pattern = os.path.expandvars(pattern)
            if "*" in exp_pattern:
                matches = glob.glob(exp_pattern, recursive=True)
                expanded.extend(matches)
            else:
                expanded.append(exp_pattern)
        return expanded

    def find_on_path(self, executable_names: List[str]) -> Optional[Tuple[str, str, int]]:
        """Tier 1: Checks PATH for candidate executable names."""
        for exe_name in executable_names:
            found_path = shutil.which(exe_name)
            if found_path:
                return (os.path.abspath(found_path), "PATH", 100)
        return None

    def find_custom_paths(self, custom_paths: List[str]) -> Optional[Tuple[str, str, int]]:
        """Tier 2: Checks user-configured custom paths."""
        for path in custom_paths:
            exp_path = os.path.expandvars(path)
            if os.path.isfile(exp_path) and os.access(exp_path, os.X_OK):
                return (os.path.abspath(exp_path), "user_configured", 100)
        return None

    def find_known_paths(self, known_patterns: List[str]) -> Optional[Tuple[str, str, int]]:
        """Tier 3: Checks known installation patterns."""
        candidate_paths = self.expand_path_patterns(known_patterns)
        for path in candidate_paths:
            if os.path.isfile(path):
                if detect_platform() == "windows" or os.access(path, os.X_OK):
                    return (os.path.abspath(path), "known_install_path", 95)
        return None

    def find_platform_paths(self, tool_id: str, exe_names: List[str]) -> Optional[Tuple[str, str, int]]:
        """Tier 4: Platform-specific default fallback search locations."""
        plat = detect_platform()
        defaults = []

        if plat == "windows":
            prog_files = os.environ.get("ProgramFiles", "C:\\Program Files")
            prog_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
            local_appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local"))
            sys_drive = os.environ.get("SystemDrive", "C:")

            if tool_id == "kicad":
                defaults = [
                    os.path.join(prog_files, "KiCad", "*", "bin", "kicad-cli.exe"),
                    os.path.join(prog_files, "KiCad", "*", "bin", "kicad.exe"),
                    os.path.join(prog_files, "KiCad", "bin", "kicad-cli.exe"),
                    os.path.join(prog_files, "KiCad", "bin", "kicad.exe"),
                    os.path.join(prog_files_x86, "KiCad", "*", "bin", "kicad-cli.exe"),
                ]
            elif tool_id == "ngspice":
                defaults = [
                    os.path.join(prog_files, "ngspice", "**", "ngspice.exe"),
                    os.path.join(prog_files, "Spice64", "**", "ngspice.exe"),
                    os.path.join(sys_drive, "\\Spice64", "**", "ngspice.exe"),
                    os.path.join(sys_drive, "\\Spice64", "bin", "ngspice.exe"),
                    os.path.join(sys_drive, "\\Spice64", "bin", "ngspice_con.exe"),
                    os.path.join(sys_drive, "\\Spice64_64", "bin", "ngspice.exe"),
                    os.path.join(local_appdata, "Programs", "ngspice", "bin", "ngspice.exe")
                ]
            elif tool_id == "python":
                defaults = [
                    os.path.join(sys_drive, "\\Python*", "python.exe"),
                    os.path.join(local_appdata, "Programs", "Python", "Python*", "python.exe"),
                    os.path.join(prog_files, "Python*", "python.exe"),
                ]
            elif tool_id == "git":
                defaults = [
                    os.path.join(prog_files, "Git", "cmd", "git.exe"),
                    os.path.join(prog_files, "Git", "bin", "git.exe"),
                    os.path.join(prog_files_x86, "Git", "cmd", "git.exe"),
                ]

        elif plat == "linux":
            for name in exe_names:
                defaults.extend([
                    f"/usr/bin/{name}",
                    f"/usr/local/bin/{name}",
                    f"/opt/{tool_id}/bin/{name}",
                    os.path.expanduser(f"~/.local/bin/{name}")
                ])

        elif plat == "macos":
            for name in exe_names:
                defaults.extend([
                    f"/usr/local/bin/{name}",
                    f"/opt/homebrew/bin/{name}",
                    f"/Applications/{tool_id.capitalize()}.app/Contents/MacOS/{name}"
                ])

        if defaults:
            res = self.find_known_paths(defaults)
            if res:
                return (res[0], "platform_search", 90)

        return None

    def query_version(self, exec_path: str, version_commands: List[List[str]]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Queries the executable version using preferred and fallback command flags."""
        if not version_commands:
            version_commands = [["--version"]]

        for ver_cmd in version_commands:
            try:
                cmd = [exec_path] + ver_cmd
                res = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=5,
                    shell=False
                )
                raw_out = (res.stdout + res.stderr).strip()
                if raw_out:
                    parsed = VersionChecker.extract_version(raw_out)
                    return raw_out, parsed, None
            except subprocess.TimeoutExpired:
                continue
            except PermissionError as e:
                return None, None, f"Permission denied: {e}"
            except Exception as e:
                return None, None, str(e)

        return None, None, "Version flag query produced no parseable output"

    def discover(self, tool_id: str, tool_def: Dict[str, Any]) -> Dict[str, Any]:
        """Discovers a tool using the 5-tier pipeline and sets VERSION_UNKNOWN when binary exists."""
        display_name = tool_def.get("display_name", tool_id.capitalize())
        plat = detect_platform()
        
        exe_names = tool_def.get("executable_names", [])
        if not exe_names:
            base_cmd = tool_def.get("command", tool_id)
            if "commands" in tool_def and isinstance(tool_def["commands"], dict):
                base_cmd = tool_def["commands"].get(plat, base_cmd)
            exe_names = [base_cmd]

        if plat == "windows":
            formatted = []
            for name in exe_names:
                formatted.append(name)
                if not name.lower().endswith(".exe"):
                    formatted.append(f"{name}.exe")
            exe_names = formatted

        known_patterns = tool_def.get(f"{plat}_paths", [])
        custom_paths = tool_def.get("custom_paths", [])

        location_info = (
            self.find_on_path(exe_names) or
            self.find_custom_paths(custom_paths) or
            self.find_known_paths(known_patterns) or
            self.find_platform_paths(tool_id, exe_names)
        )

        result = {
            "tool_id": tool_id,
            "display_name": display_name,
            "found": False,
            "installed": False,
            "executable_path": None,
            "source": "NOT_FOUND",
            "confidence": 0,
            "raw_version": None,
            "parsed_version": None,
            "status": "MISSING",
            "error": None,
            "required": tool_def.get("required", False),
            "importance": tool_def.get("importance", "OPTIONAL"),
            "minimum_version": tool_def.get("minimum_version", "0.0.0")
        }

        if not location_info:
            self.logger.warning(f"Tool discovery: '{display_name}' NOT found on system")
            return result

        path, source, confidence = location_info
        result["found"] = True
        result["installed"] = True
        result["executable_path"] = path
        result["source"] = source
        result["confidence"] = confidence

        # Version querying
        ver_cmds = []
        if "version_command" in tool_def:
            ver_cmds.append(tool_def["version_command"])
        if "version_commands" in tool_def:
            ver_cmds.extend(tool_def["version_commands"])
        if "version_arguments" in tool_def:
            ver_cmds.append(tool_def["version_arguments"])
            
        if not ver_cmds:
            ver_cmds = [["--version"], ["version"], ["-v"], ["-V"]]

        raw_v, parsed_v, err = self.query_version(path, ver_cmds)
        result["raw_version"] = raw_v
        result["parsed_version"] = parsed_v
        result["error"] = err

        if parsed_v:
            result["status"] = "DETECTED"
            self.logger.info(f"Tool discovery: '{display_name}' ({parsed_v}) detected via {source} at {path}")
        else:
            # Binary exists on disk, but version string could not be extracted
            result["status"] = "VERSION_UNKNOWN"
            self.logger.warning(f"Tool discovery: '{display_name}' binary detected via {source} at {path} (version string unknown)")

        return result

    def discover_all(self, tools_config: Dict[str, Dict[str, Any]] = None) -> Dict[str, Dict[str, Any]]:
        """Discovers all tools in the configuration dictionary."""
        tools_to_check = tools_config if tools_config is not None else self.tools
        self.logger.info("Layered tool discovery pipeline started")
        results = {}
        for tool_id, tool_def in tools_to_check.items():
            results[tool_id] = self.discover(tool_id, tool_def)
        self.logger.info("Layered tool discovery pipeline finished")
        return results
