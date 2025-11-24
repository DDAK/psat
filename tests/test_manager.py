"""Tests for the LinterManager class."""

from pathlib import Path

import pytest

from ast_import_analyzer.manager import ImportIssue, LinterManager


class TestImportIssue:
    """Test suite for ImportIssue."""

    def test_str_representation(self):
        """Test string representation of ImportIssue."""
        issue = ImportIssue(
            file=Path("/path/to/file.py"),
            import_path="missing.module",
            message="Module not found",
            issue_type="EXTERNAL",
        )

        result = str(issue)

        assert "[EXTERNAL]" in result
        assert "/path/to/file.py" in result
        assert "Module not found" in result


class TestLinterManager:
    """Test suite for LinterManager."""

    def test_init_default_excluded_dirs(self, tmp_path: Path):
        """Test that default excluded directories are set."""
        manager = LinterManager(str(tmp_path))

        assert "__pycache__" in manager.excluded_dirs
        assert ".git" in manager.excluded_dirs
        assert "venv" in manager.excluded_dirs
        assert ".venv" in manager.excluded_dirs

    def test_init_custom_excluded_dirs(self, tmp_path: Path):
        """Test adding custom excluded directories."""
        manager = LinterManager(
            str(tmp_path),
            excluded_dirs={"custom_dir", "another_dir"},
        )

        assert "custom_dir" in manager.excluded_dirs
        assert "another_dir" in manager.excluded_dirs
        # Default dirs should still be present
        assert "__pycache__" in manager.excluded_dirs

    def test_run_nonexistent_path(self, tmp_path: Path):
        """Test that FileNotFoundError is raised for missing paths."""
        manager = LinterManager(str(tmp_path / "nonexistent"))

        with pytest.raises(FileNotFoundError):
            manager.run()

    def test_run_empty_directory(self, tmp_path: Path):
        """Test running on an empty directory."""
        manager = LinterManager(str(tmp_path))
        issues = manager.run()

        assert issues == []
        assert len(manager.file_imports) == 0

    def test_run_single_file(self, tmp_path: Path):
        """Test running on a single Python file."""
        file_path = tmp_path / "single.py"
        file_path.write_text("import os\n\ndef main():\n    pass\n")

        manager = LinterManager(str(file_path))
        manager.run()

        assert file_path in manager.file_imports
        assert "os" in manager.file_imports[file_path]
        assert "main" in manager.module_defs[file_path]

    def test_run_directory_with_files(self, tmp_path: Path):
        """Test running on a directory with multiple Python files."""
        (tmp_path / "file1.py").write_text("import os\n")
        (tmp_path / "file2.py").write_text("import sys\n")

        manager = LinterManager(str(tmp_path))
        manager.run()

        assert len(manager.file_imports) == 2

    def test_excludes_pycache(self, tmp_path: Path):
        """Test that __pycache__ directories are excluded."""
        pycache = tmp_path / "__pycache__"
        pycache.mkdir()
        (pycache / "cached.py").write_text("import os\n")
        (tmp_path / "main.py").write_text("import sys\n")

        manager = LinterManager(str(tmp_path))
        manager.run()

        # Only main.py should be analyzed
        assert len(manager.file_imports) == 1
        assert tmp_path / "main.py" in manager.file_imports

    def test_excludes_venv(self, tmp_path: Path):
        """Test that venv directories are excluded."""
        venv = tmp_path / "venv"
        venv.mkdir()
        (venv / "lib.py").write_text("import os\n")
        (tmp_path / "main.py").write_text("import sys\n")

        manager = LinterManager(str(tmp_path))
        manager.run()

        assert len(manager.file_imports) == 1

    def test_analyze_file_with_syntax_error(self, tmp_path: Path):
        """Test that files with syntax errors are skipped gracefully."""
        (tmp_path / "valid.py").write_text("import os\n")
        (tmp_path / "invalid.py").write_text("def broken(\n")

        manager = LinterManager(str(tmp_path))
        manager.run()

        # Only valid.py should be in the results
        assert len(manager.file_imports) == 1

    def test_subdirectory_traversal(self, tmp_path: Path):
        """Test that subdirectories are traversed."""
        subdir = tmp_path / "subpackage"
        subdir.mkdir()
        (subdir / "__init__.py").write_text("")
        (subdir / "module.py").write_text("import json\n")
        (tmp_path / "main.py").write_text("import os\n")

        manager = LinterManager(str(tmp_path))
        manager.run()

        assert len(manager.file_imports) == 3  # main.py, __init__.py, module.py

    def test_print_report_no_issues(self, tmp_path: Path, capsys):
        """Test print_report with no issues."""
        (tmp_path / "clean.py").write_text("import os\n")

        manager = LinterManager(str(tmp_path))
        manager.run()
        manager.print_report()

        captured = capsys.readouterr()
        assert "No import issues found" in captured.out

    def test_print_report_with_issues(self, tmp_path: Path, capsys):
        """Test print_report with issues."""
        manager = LinterManager(str(tmp_path))
        manager.issues = [
            ImportIssue(
                file=Path("/test.py"),
                import_path="missing.module",
                message="Not found",
                issue_type="EXTERNAL",
            )
        ]
        manager.file_imports = {Path("/test.py"): set()}
        manager.print_report()

        captured = capsys.readouterr()
        assert "Import Analysis Report" in captured.out
        assert "Issues found: 1" in captured.out

    def test_auto_fix_disabled_by_default(self, tmp_path: Path):
        """Test that auto_fix is disabled by default."""
        manager = LinterManager(str(tmp_path))
        assert manager.auto_fix is False

    def test_auto_fix_can_be_enabled(self, tmp_path: Path):
        """Test that auto_fix can be enabled."""
        manager = LinterManager(str(tmp_path), auto_fix=True)
        assert manager.auto_fix is True
