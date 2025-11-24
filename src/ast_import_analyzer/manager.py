"""Linter manager for analyzing import dependencies across a codebase."""

import logging
import os
from pathlib import Path

from .analyzer import PythonFileAnalyzer
from .utils import VirtualEnvChecker, pre_cleanup_with_ruff, validate_import

logger = logging.getLogger(__name__)


class ImportIssue:
    """Represents an import validation issue."""

    __slots__ = ("file", "import_path", "message", "issue_type")

    def __init__(self, file: Path, import_path: str, message: str, issue_type: str) -> None:
        self.file = file
        self.import_path = import_path
        self.message = message
        self.issue_type = issue_type

    def __str__(self) -> str:
        return f"[{self.issue_type}] {self.file}: {self.message}"


class LinterManager:
    """
    Orchestrates import analysis across a directory tree.

    Analyzes Python files to detect:
    - Dangling imports (imports that don't resolve)
    - Missing module attributes
    - Uninstalled packages
    """

    DEFAULT_EXCLUDED_DIRS: set[str] = {
        "__pycache__",
        ".git",
        ".gitlab",
        ".github",
        ".idea",
        ".venv",
        "venv",
        "env",
        ".env",
        "node_modules",
        "build",
        "dist",
        ".eggs",
        "*.egg-info",
        "alembic",
        "migrations",
    }

    __slots__ = (
        "root_path",
        "venv_checker",
        "module_defs",
        "file_imports",
        "issues",
        "excluded_dirs",
        "auto_fix",
    )

    def __init__(
        self,
        path: str,
        excluded_dirs: set[str] | None = None,
        auto_fix: bool = False,
    ) -> None:
        """
        Initialize the linter manager.

        Args:
            path: Root path to analyze.
            excluded_dirs: Additional directories to exclude from analysis.
            auto_fix: Whether to run ruff auto-fix before analysis.
        """
        self.root_path = Path(path).absolute()
        self.venv_checker = VirtualEnvChecker()
        self.module_defs: dict[Path, set[str]] = {}
        self.file_imports: dict[Path, set[str]] = {}
        self.issues: list[ImportIssue] = []
        self.excluded_dirs = self.DEFAULT_EXCLUDED_DIRS.copy()
        if excluded_dirs:
            self.excluded_dirs.update(excluded_dirs)
        self.auto_fix = auto_fix

    def run(self) -> list[ImportIssue]:
        """
        Run the analysis on the configured path.

        Returns:
            List of import issues found.

        Raises:
            FileNotFoundError: If the path does not exist.
        """
        if not self.root_path.exists():
            raise FileNotFoundError(f"Path not found: {self.root_path}")

        self._collect_files()
        self._validate_imports()

        return self.issues

    def _collect_files(self) -> None:
        """Collect and analyze all Python files in the directory tree."""
        if self.root_path.is_file():
            self._analyze_file(self.root_path)
        elif self.root_path.is_dir():
            self._analyze_directory()

    def _analyze_file(self, file_path: Path) -> None:
        """
        Analyze a single Python file.

        Args:
            file_path: Path to the Python file.
        """
        if self.auto_fix:
            pre_cleanup_with_ruff(file_path)

        try:
            analyzer = PythonFileAnalyzer(file_path)
            analyzer.analyze()
            self.file_imports[file_path] = analyzer.imported_modules
            self.module_defs[file_path] = analyzer.module_defs
        except SyntaxError as err:
            logger.warning("Syntax error in %s: %s", file_path, err)
        except Exception as err:
            logger.error("Error analyzing %s: %s", file_path, err)

    def _analyze_directory(self) -> None:
        """Walk the directory tree and analyze Python files."""
        for dirpath, dirnames, filenames in os.walk(self.root_path):
            # Filter out excluded directories
            dirnames[:] = [
                d
                for d in dirnames
                if d not in self.excluded_dirs and not self.venv_checker.is_venv(Path(dirpath) / d)
            ]

            for filename in filenames:
                if filename.endswith(".py"):
                    file_path = Path(dirpath) / filename
                    self._analyze_file(file_path)

    def _validate_imports(self) -> None:
        """Validate all collected imports against defined modules."""
        for file_path, imports in self.file_imports.items():
            for imp in imports:
                issue = self._check_import(file_path, imp)
                if issue:
                    self.issues.append(issue)

    def _check_import(self, file_path: Path, import_path: str) -> ImportIssue | None:
        """
        Check if an import is valid.

        Args:
            file_path: The file containing the import.
            import_path: The dotted import path.

        Returns:
            ImportIssue if validation failed, None otherwise.
        """
        parts = import_path.split(".")
        if not parts:
            return None

        attr_name = parts[-1]
        module_parts = parts[:-1]

        # Try to resolve as a local project import
        # Check if it's a file in the project
        if module_parts:
            possible_file = self.root_path / "/".join(module_parts) / f"{attr_name}.py"
            if possible_file in self.file_imports:
                # It's importing a module file - valid
                return None

            possible_file = self.root_path / "/".join(module_parts + [attr_name]) / "__init__.py"
            if possible_file.exists():
                # It's importing a package - valid
                return None

            module_file = self.root_path / "/".join(module_parts) + ".py"
            if module_file in self.module_defs:
                defs = self.module_defs[module_file]
                if attr_name not in defs:
                    return ImportIssue(
                        file=file_path,
                        import_path=import_path,
                        message=f"'{'.'.join(module_parts)}' does not define '{attr_name}'",
                        issue_type="UNDEFINED",
                    )
                return None

        # Check as external import
        error = validate_import(import_path, str(file_path))
        if error:
            return ImportIssue(
                file=file_path,
                import_path=import_path,
                message=error,
                issue_type="EXTERNAL",
            )

        return None

    def print_report(self) -> None:
        """Print a summary report of issues found."""
        if not self.issues:
            print(f"No import issues found in {self.root_path}")
            return

        print(f"\nImport Analysis Report: {self.root_path}")
        print("=" * 60)
        print(f"Files analyzed: {len(self.file_imports)}")
        print(f"Issues found: {len(self.issues)}")
        print("-" * 60)

        for issue in self.issues:
            print(issue)


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze Python imports for issues",
        prog="ast-import-analyzer",
    )
    parser.add_argument("path", help="Path to analyze (file or directory)")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Run ruff auto-fix before analysis",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="Additional directories to exclude",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    manager = LinterManager(
        path=args.path,
        excluded_dirs=set(args.exclude) if args.exclude else None,
        auto_fix=args.fix,
    )

    try:
        manager.run()
        manager.print_report()
    except FileNotFoundError as err:
        print(f"Error: {err}")
        exit(1)


if __name__ == "__main__":
    main()
