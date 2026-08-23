import re
from typing import List

class VersionChecker:
    @staticmethod
    def extract_version(version_string: str) -> str:
        """Extracts the first numeric/semantic version found in a string.
        
        Args:
            version_string (str): Raw version output from a command line.
            
        Returns:
            str: Extracted version string or None.
        """
        if not version_string:
            return None
        
        # Look for typical dot-separated version patterns, e.g. 3.12.4, 9.0
        match = re.search(r"\d+(?:\.\d+)+", version_string)
        if match:
            return match.group(0)
            
        # Fallback to single integers if no dots exist, e.g. "Ngspice 30" -> "30"
        match_single = re.search(r"\d+", version_string)
        if match_single:
            return match_single.group(0)
            
        return None

    @staticmethod
    def normalize_version(version: str) -> List[int]:
        """Normalizes a version string into a list of integer components.
        
        Args:
            version (str): Version string.
            
        Returns:
            List[int]: List of version components as integers.
        """
        if not version:
            return []
            
        # Clean any trailing characters that aren't digits or dots
        clean = re.sub(r"[^\d.]", "", version)
        parts = clean.split(".")
        
        result = []
        for p in parts:
            if p.strip().isdigit():
                result.append(int(p))
        return result

    @staticmethod
    def compare_versions(current: str, minimum: str) -> int:
        """Compares a current version string with a minimum required version.
        
        Args:
            current (str): The current version.
            minimum (str): The minimum required version.
            
        Returns:
            int: 1 if current > minimum, 0 if current == minimum, -1 if current < minimum.
            
        Raises:
            ValueError: If either version is not parseable.
        """
        curr_parts = VersionChecker.normalize_version(current)
        min_parts = VersionChecker.normalize_version(minimum)
        
        if not curr_parts or not min_parts:
            raise ValueError(f"Cannot compare invalid version formats. Current: '{current}', Minimum: '{minimum}'")
            
        max_len = max(len(curr_parts), len(min_parts))
        
        # Pad lists with zeros to match lengths
        curr_padded = curr_parts + [0] * (max_len - len(curr_parts))
        min_padded = min_parts + [0] * (max_len - len(min_parts))
        
        for c, m in zip(curr_padded, min_padded):
            if c > m:
                return 1
            elif c < m:
                return -1
        return 0

    @staticmethod
    def is_compatible(current: str, minimum: str) -> bool:
        """Checks if current version is greater than or equal to minimum.
        
        Args:
            current (str): Current version.
            minimum (str): Minimum required version.
            
        Returns:
            bool: True if current satisfies minimum, False otherwise.
        """
        if not current or not minimum:
            return False
        try:
            return VersionChecker.compare_versions(current, minimum) >= 0
        except ValueError:
            return False