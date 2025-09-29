import os
from pathlib import Path
import time


class FileService:
    def __init__(self, base_directory: str):
        self.base_directory = Path(base_directory).resolve()

    def _resolve_path(self, path: str) -> Path:
        """Resolve and ensure the path is within the allowed base directory."""
        full_path = (self.base_directory / path).resolve()
        if not str(full_path).startswith(str(self.base_directory)):
            return None
        return full_path

    def write_to_file(self, path: str, content: str) -> str:
        """Write content to a file at the specified path."""
        try:
            p = self._resolve_path(path)
            if p is None:
                return f"Access to the specified path '{path}' is not allowed."
            if p.exists():
                backup_path = p.with_suffix(p.suffix + f".paircode.{time.time()}.bak")
                p.rename(backup_path)
            with p.open("w") as f:
                f.write(content)
            return f"Wrote to {p}"
        except Exception as e:
            return f"Error writing to {path}: {e}"

    def read_file(self, path: str) -> str:
        """Read and return the content of a file at the specified path."""
        try:
            p = self._resolve_path(path)
            if p is None:
                return f"Access to the specified path '{path}' is not allowed."
            with p.open("r") as f:
                return f.read()
        except Exception as e:
            return f"Error reading {path}: {e}"

    def list_files(self, directory: str) -> str:
        """List files in the specified directory."""
        try:
            p = self._resolve_path(directory)
            if p is None:
                return f"Access to the specified directory '{directory}' is not allowed."
            files = os.listdir(p)
            return "\n".join(files)
        except Exception as e:
            return f"Error listing files in {directory}: {e}"
