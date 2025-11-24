"""Tests for the PythonFileAnalyzer class."""

import tempfile
from pathlib import Path

import pytest

from ast_import_analyzer.analyzer import PythonFileAnalyzer


class TestPythonFileAnalyzer:
    """Test suite for PythonFileAnalyzer."""

    def test_analyze_simple_file(self, tmp_path: Path):
        """Test analyzing a simple Python file."""
        file_path = tmp_path / "simple.py"
        file_path.write_text("import os\n\ndef hello():\n    pass\n")

        analyzer = PythonFileAnalyzer(file_path)
        analyzer.analyze()

        assert "os" in analyzer.imported_modules
        assert "hello" in analyzer.module_defs

    def test_analyze_file_with_class(self, tmp_path: Path):
        """Test analyzing a file with a class definition."""
        file_path = tmp_path / "with_class.py"
        file_path.write_text("""
from typing import Optional

class MyService:
    def __init__(self):
        pass

    def process(self):
        pass

SERVICE_INSTANCE = None
""")

        analyzer = PythonFileAnalyzer(file_path)
        analyzer.analyze()

        assert "typing.Optional" in analyzer.imported_modules
        assert "MyService" in analyzer.module_defs
        assert "SERVICE_INSTANCE" in analyzer.module_defs

    def test_analyze_file_not_found(self, tmp_path: Path):
        """Test that FileNotFoundError is raised for missing files."""
        file_path = tmp_path / "nonexistent.py"

        analyzer = PythonFileAnalyzer(file_path)

        with pytest.raises(FileNotFoundError):
            analyzer.analyze()

    def test_analyze_syntax_error(self, tmp_path: Path):
        """Test that SyntaxError is raised for invalid Python."""
        file_path = tmp_path / "invalid.py"
        file_path.write_text("def broken(\n")

        analyzer = PythonFileAnalyzer(file_path)

        with pytest.raises(SyntaxError):
            analyzer.analyze()

    def test_analyze_empty_file(self, tmp_path: Path):
        """Test analyzing an empty file."""
        file_path = tmp_path / "empty.py"
        file_path.write_text("")

        analyzer = PythonFileAnalyzer(file_path)
        analyzer.analyze()

        assert len(analyzer.imported_modules) == 0
        assert len(analyzer.module_defs) == 0

    def test_analyze_complex_imports(self, tmp_path: Path):
        """Test analyzing a file with complex imports."""
        file_path = tmp_path / "complex.py"
        file_path.write_text("""
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict
from collections.abc import Iterator

from .local import helper
from ..parent import util
""")

        analyzer = PythonFileAnalyzer(file_path)
        analyzer.analyze()

        assert "os" in analyzer.imported_modules
        assert "sys" in analyzer.imported_modules
        assert "pathlib.Path" in analyzer.imported_modules
        assert "typing.Optional" in analyzer.imported_modules
        assert "typing.List" in analyzer.imported_modules
        assert "typing.Dict" in analyzer.imported_modules
        assert "collections.abc.Iterator" in analyzer.imported_modules
        assert "local.helper" in analyzer.imported_modules
        assert "parent.util" in analyzer.imported_modules

    def test_analyze_utf8_file(self, tmp_path: Path):
        """Test analyzing a file with UTF-8 content."""
        file_path = tmp_path / "utf8.py"
        file_path.write_text('# -*- coding: utf-8 -*-\n"""Модуль с Unicode."""\n\ndef привет():\n    pass\n', encoding="utf-8")

        analyzer = PythonFileAnalyzer(file_path)
        analyzer.analyze()

        assert "привет" in analyzer.module_defs

    def test_file_path_stored(self, tmp_path: Path):
        """Test that file_path is correctly stored."""
        file_path = tmp_path / "test.py"
        file_path.write_text("x = 1")

        analyzer = PythonFileAnalyzer(file_path)

        assert analyzer.file_path == file_path

    def test_initial_state(self, tmp_path: Path):
        """Test that initial state has empty sets."""
        file_path = tmp_path / "test.py"
        file_path.write_text("x = 1")

        analyzer = PythonFileAnalyzer(file_path)

        assert analyzer.imported_modules == set()
        assert analyzer.module_defs == set()
