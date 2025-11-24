"""Tests for utility functions."""

from pathlib import Path
from unittest.mock import patch

import pytest

from ast_import_analyzer.utils import (
    VirtualEnvChecker,
    get_installed_packages,
    run_subprocess,
    validate_import,
)


class TestRunSubprocess:
    """Test suite for run_subprocess."""

    def test_successful_command(self):
        """Test running a successful command."""
        result = run_subprocess(["echo", "hello"])

        assert result is not None
        assert result.returncode == 0
        assert "hello" in result.stdout

    def test_command_not_found(self):
        """Test handling of non-existent command."""
        result = run_subprocess(["nonexistent_command_xyz"])

        assert result is None

    def test_command_with_error(self):
        """Test command that exits with error."""
        result = run_subprocess(["python", "-c", "import sys; sys.exit(1)"])

        assert result is not None
        assert result.returncode == 1


class TestValidateImport:
    """Test suite for validate_import."""

    def test_valid_stdlib_import(self):
        """Test validation of valid stdlib import."""
        result = validate_import("os")

        assert result is None

    def test_valid_stdlib_attribute(self):
        """Test validation of valid stdlib attribute."""
        result = validate_import("os.path")

        assert result is None

    def test_valid_nested_import(self):
        """Test validation of nested module import."""
        result = validate_import("os.path.join")

        assert result is None

    def test_invalid_module(self):
        """Test validation of non-existent module."""
        result = validate_import("nonexistent_module_xyz")

        assert result is not None
        assert "Module not found" in result

    def test_invalid_attribute(self):
        """Test validation of non-existent attribute."""
        result = validate_import("os.nonexistent_function_xyz")

        assert result is not None
        assert "has no attribute" in result

    def test_empty_path(self):
        """Test validation of empty path."""
        result = validate_import("")

        assert result == "Empty import path"

    def test_source_file_context(self):
        """Test that source file is included in error context."""
        result = validate_import("nonexistent_module", source_file="test.py")

        assert result is not None
        assert "test.py" in result


class TestGetInstalledPackages:
    """Test suite for get_installed_packages."""

    def test_returns_set(self):
        """Test that function returns a set."""
        result = get_installed_packages()

        assert isinstance(result, set)

    def test_packages_are_lowercase(self):
        """Test that package names are lowercased."""
        result = get_installed_packages()

        for pkg in result:
            assert pkg == pkg.lower()

    @patch("ast_import_analyzer.utils.subprocess.run")
    def test_handles_pip_failure(self, mock_run):
        """Test handling of pip failure."""
        mock_run.return_value.returncode = 1

        result = get_installed_packages()

        assert result == set()


class TestVirtualEnvChecker:
    """Test suite for VirtualEnvChecker."""

    def test_non_directory(self, tmp_path: Path):
        """Test that non-directories return False."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")

        checker = VirtualEnvChecker()

        assert checker.is_venv(file_path) is False

    def test_empty_directory(self, tmp_path: Path):
        """Test that empty directory returns False."""
        checker = VirtualEnvChecker()

        assert checker.is_venv(tmp_path) is False

    def test_venv_with_pyvenv_cfg(self, tmp_path: Path):
        """Test detection of venv with pyvenv.cfg."""
        venv_dir = tmp_path / "venv"
        venv_dir.mkdir()
        (venv_dir / "pyvenv.cfg").write_text("home = /usr/bin")
        (venv_dir / "bin").mkdir()
        (venv_dir / "include").mkdir()
        (venv_dir / "lib").mkdir()

        checker = VirtualEnvChecker()

        assert checker.is_venv(venv_dir) is True

    def test_partial_venv_structure(self, tmp_path: Path):
        """Test that partial venv structure returns False."""
        venv_dir = tmp_path / "partial_venv"
        venv_dir.mkdir()
        (venv_dir / "bin").mkdir()
        # Missing other indicators

        checker = VirtualEnvChecker()

        assert checker.is_venv(venv_dir) is False

    def test_regular_project_directory(self, tmp_path: Path):
        """Test that regular project directory returns False."""
        project = tmp_path / "project"
        project.mkdir()
        (project / "src").mkdir()
        (project / "tests").mkdir()
        (project / "README.md").write_text("# Project")

        checker = VirtualEnvChecker()

        assert checker.is_venv(project) is False

    def test_venv_indicators_defined(self):
        """Test that venv indicators are defined for common platforms."""
        checker = VirtualEnvChecker()

        assert "linux" in checker.VENV_INDICATORS
        assert "darwin" in checker.VENV_INDICATORS
        assert "win32" in checker.VENV_INDICATORS
