"""Open local files with the platform default handler."""
import os
import subprocess
import sys


def open_local_path(path: str) -> None:
    """Open a file or directory using the OS default application.

    Raises OSError (or subclass) if the platform handler cannot be invoked.
    """
    if not path:
        raise ValueError("path is required")

    # Windows
    if hasattr(os, "startfile"):
        os.startfile(path)  # type: ignore[attr-defined]
        return

    # macOS
    if sys.platform == "darwin":
        result = subprocess.run(["open", path], check=False, capture_output=True)
        if result.returncode != 0:
            detail = (result.stderr or result.stdout or b"").decode(errors="replace").strip()
            raise OSError(detail or f"open failed for {path}")
        return

    # Linux and other Unix-like systems
    result = subprocess.run(["xdg-open", path], check=False, capture_output=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or b"").decode(errors="replace").strip()
        raise OSError(detail or f"xdg-open failed for {path}")
