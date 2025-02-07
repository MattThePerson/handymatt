import os
import re

def is_windows_path(path: str) -> bool:
    """Detects if a given path is a Windows path."""
    return bool(re.match(r"^[a-zA-Z]:\\", path))  # Matches "C:\", "D:\", etc.

def convert_to_wsl_path(path: str) -> str:
    """Converts a Windows path to a WSL path if running inside WSL."""
    if "WSL_DISTRO_NAME" in os.environ and is_windows_path(path):
        drive, rest = path[0].lower(), path[2:].replace("\\", "/")
        return f"/mnt/{drive}/{rest}"
    return path  # Return unchanged if not in WSL or not a Windows path
