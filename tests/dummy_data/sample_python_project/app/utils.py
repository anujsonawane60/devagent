"""Utility functions for the application."""

import os
import json
from pathlib import Path
from typing import Any, Dict, List


def read_json(file_path: str) -> Dict[str, Any]:
    """Read and parse a JSON file."""
    with open(file_path, "r") as f:
        return json.load(f)


def write_json(file_path: str, data: Dict[str, Any]) -> None:
    """Write data to a JSON file."""
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)


def ensure_directory(path: str) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def flatten_list(nested: List[List[Any]]) -> List[Any]:
    """Flatten a nested list into a single list."""
    return [item for sublist in nested for item in sublist]


class FileProcessor:
    """Processes files in a directory."""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)

    def list_files(self, extension: str = "") -> List[str]:
        """List files in the base directory."""
        if extension:
            return [str(f) for f in self.base_dir.glob(f"*{extension}")]
        return [str(f) for f in self.base_dir.iterdir() if f.is_file()]

    def count_lines(self, file_path: str) -> int:
        """Count lines in a file."""
        with open(file_path, "r") as f:
            return sum(1 for _ in f)
