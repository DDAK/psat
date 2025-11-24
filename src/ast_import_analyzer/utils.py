"""Utility functions for import analysis."""

import logging
import subprocess
import sys
from importlib import import_module
from pathlib import Path

logger = logging.getLogger(__name__)


def run_subprocess(command: list[str]) -> subprocess.CompletedProcess | None:
    """
    Run a subprocess command safely.

    Args:
        command: Command and arguments to execute.

    Returns:
        CompletedProcess result or None if execution failed.
    """
    try:
        return subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        logger.warning("Command not found: %s", command[0])
        return None
    except Exception as ex:
        logger.error("Subprocess error: %s", ex)
        return None


def pre_cleanup_with_ruff(path: Path) -> bool:
    """
    Run ruff linter with auto-fix on a file.

    Args:
        path: Path to the file to lint.

    Returns:
        True if ruff ran successfully, False otherwise.
    """
    result = run_subprocess(["ruff", "check", str(path), "--fix"])
    return result is not None and result.returncode == 0


def get_installed_packages() -> set[str]:
    """
    Get the set of currently installed packages.

    Returns:
        Set of package names (lowercase, without versions).
    """
    result = subprocess.run(
        [sys.executable, "-m", "pip", "freeze"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return set()

    packages = set()
    for line in result.stdout.strip().split("\n"):
        if "==" in line:
            packages.add(line.split("==")[0].lower())
        elif line.strip():
            packages.add(line.strip().lower())
    return packages


def validate_import(dotted_path: str, source_file: str | None = None) -> str | None:
    """
    Validate that a dotted import path resolves to an actual module/attribute.

    Args:
        dotted_path: The import path to validate (e.g., "os.path.join").
        source_file: Optional source file for error context.

    Returns:
        Error message if validation failed, None if successful.
    """
    if not dotted_path:
        return "Empty import path"

    if "." in dotted_path:
        module_path, attr_name = dotted_path.rsplit(".", 1)
    else:
        module_path = dotted_path
        attr_name = ""

    try:
        module = import_module(module_path)
        if attr_name and not hasattr(module, attr_name):
            ctx = f" in {source_file}" if source_file else ""
            return f"Module '{module_path}' has no attribute '{attr_name}'{ctx}"
    except ModuleNotFoundError as err:
        ctx = f" in {source_file}" if source_file else ""
        return f"Module not found: '{module_path}'{ctx} ({err})"
    except Exception as err:
        return f"Import error for '{dotted_path}': {err}"

    return None


class VirtualEnvChecker:
    """Utility to detect virtual environment directories."""

    VENV_INDICATORS = {
        "linux": {"bin", "include", "lib", "pyvenv.cfg"},
        "linux2": {"bin", "include", "lib", "pyvenv.cfg"},
        "darwin": {"bin", "include", "lib", "pyvenv.cfg"},
        "win32": {"Scripts", "Include", "Lib", "pyvenv.cfg"},
    }

    def is_venv(self, path: Path) -> bool:
        """
        Check if a path is likely a virtual environment.

        Args:
            path: Directory path to check.

        Returns:
            True if the path appears to be a virtual environment.
        """
        if not path.is_dir():
            return False

        indicators = self.VENV_INDICATORS.get(sys.platform, set())
        if not indicators:
            # Fallback: check for pyvenv.cfg which is always present
            return (path / "pyvenv.cfg").exists()

        return all((path / ind).exists() for ind in indicators)
