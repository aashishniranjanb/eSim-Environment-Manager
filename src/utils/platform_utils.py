import platform
import shutil

def detect_platform() -> str:
    """Detects the current operating system.
    
    Returns:
        str: 'windows', 'linux', or 'macos'.
    """
    sys_name = platform.system().lower()
    if "windows" in sys_name:
        return "windows"
    elif "darwin" in sys_name:
        return "macos"
    else:
        return "linux"

def get_default_package_manager() -> str:
    """Returns the default package manager name for the current platform."""
    plat = detect_platform()
    if plat == "windows":
        return "winget"
    elif plat == "macos":
        return "brew"
    else:
        return "apt"

def is_package_manager_available(pm: str = None) -> bool:
    """Checks if a given package manager (or the default one) is available on the system."""
    if pm is None:
        pm = get_default_package_manager()
    return shutil.which(pm) is not None

