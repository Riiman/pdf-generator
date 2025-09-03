import os
import re
import sys
from pathlib import Path


def resource_path(relative_path: str) -> str:
    """
    Resolve path to resource bundled by PyInstaller. Falls back to local path.
    """
    base_path = getattr(sys, "_MEIPASS", None)
    if base_path:
        return str(Path(base_path, relative_path))
    return str(Path(__file__).resolve().parent.parent / relative_path)


def find_wkhtmltopdf_path() -> str:
    """
    Locate bundled wkhtmltopdf.exe (Windows). Searches common bundled locations.
    """
    candidates = [
        resource_path("bin/wkhtmltopdf.exe"),
        resource_path("wkhtmltopdf/wkhtmltopdf.exe"),
        resource_path("third_party/wkhtmltopdf/wkhtmltopdf.exe"),
    ]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    # Fallback to PATH if available
    return "wkhtmltopdf"


def ensure_directory(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


_INVALID_CHARS_PATTERN = re.compile(r"[\\/:*?\"<>|]+")


def safe_filename(name: str, replacement: str = "_") -> str:
    sanitized = _INVALID_CHARS_PATTERN.sub(replacement, name.strip())
    sanitized = sanitized.strip(". ")
    if not sanitized:
        sanitized = "output"
    return sanitized


def unique_path(base_dir: str, filename_without_ext: str, ext: str) -> str:
    base_dir_path = Path(base_dir)
    base_dir_path.mkdir(parents=True, exist_ok=True)
    candidate = base_dir_path / f"{filename_without_ext}{ext}"
    counter = 1
    while candidate.exists():
        candidate = base_dir_path / f"{filename_without_ext} ({counter}){ext}"
        counter += 1
    return str(candidate)
