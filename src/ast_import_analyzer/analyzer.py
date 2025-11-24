"""Python file analyzer for extracting imports and definitions."""

import ast
from pathlib import Path

from .visitor import ImportsVisitor


class PythonFileAnalyzer:
    """
    Analyzes a Python file to extract imported modules and defined symbols.

    Attributes:
        file_path: Path to the Python file to analyze.
        imported_modules: Set of imported module paths after analysis.
        module_defs: Set of defined symbols after analysis.
    """

    __slots__ = ("file_path", "imported_modules", "module_defs")

    def __init__(self, file_path: Path) -> None:
        """
        Initialize the analyzer.

        Args:
            file_path: Path to the Python file to analyze.
        """
        self.file_path = file_path
        self.imported_modules: set[str] = set()
        self.module_defs: set[str] = set()

    def analyze(self) -> None:
        """
        Analyze the Python file and extract imports and definitions.

        Raises:
            FileNotFoundError: If the file does not exist.
            SyntaxError: If the file contains invalid Python syntax.
        """
        code = self.file_path.read_text(encoding="utf-8")
        tree = ast.parse(code, filename=str(self.file_path))
        visitor = ImportsVisitor()
        visitor.visit(tree)
        self.imported_modules = visitor.imported_modules
        self.module_defs = visitor.module_defs
