# AST Import Analyzer

A Python static analysis tool that detects import issues in your codebase using Abstract Syntax Tree (AST) parsing.

## Features

- **Dangling Import Detection**: Find imports that reference non-existent modules or attributes
- **Missing Attribute Detection**: Identify imports of names not defined in the source module
- **External Package Validation**: Check if imported external packages are installed
- **Directory Traversal**: Recursively analyze entire project directories
- **Virtual Environment Aware**: Automatically skips virtual environment directories

## Installation

```bash
# From source
git clone https://github.com/yourusername/ast-import-analyzer.git
cd ast-import-analyzer
pip install -e .

# With development dependencies
pip install -e ".[dev]"
```

## Usage

### Command Line

```bash
# Analyze a directory
ast-import-analyzer /path/to/your/project

# Analyze with verbose output
ast-import-analyzer /path/to/your/project -v

# Run ruff auto-fix before analysis
ast-import-analyzer /path/to/your/project --fix

# Exclude specific directories
ast-import-analyzer /path/to/your/project --exclude tests fixtures
```

### Python API

```python
from pathlib import Path
from ast_import_analyzer import LinterManager, PythonFileAnalyzer

# Analyze a single file
analyzer = PythonFileAnalyzer(Path("mymodule.py"))
analyzer.analyze()
print(f"Imports: {analyzer.imported_modules}")
print(f"Definitions: {analyzer.module_defs}")

# Analyze an entire project
manager = LinterManager("/path/to/project")
issues = manager.run()

for issue in issues:
    print(f"{issue.issue_type}: {issue.file} - {issue.message}")

# Or use the built-in report
manager.print_report()
```

### Example Output

```
Import Analysis Report: /path/to/project
============================================================
Files analyzed: 42
Issues found: 3
------------------------------------------------------------
[UNDEFINED] /path/to/project/app/utils.py: 'app.services' does not define 'missing_func'
[EXTERNAL] /path/to/project/app/main.py: Module not found: 'nonexistent_package'
[EXTERNAL] /path/to/project/app/api.py: Module 'requests' has no attribute 'fake_method'
```

## Configuration

The tool uses sensible defaults but can be customized:

### Excluded Directories

By default, these directories are skipped:
- `__pycache__`, `.git`, `.github`, `.gitlab`
- `venv`, `.venv`, `env`, `.env`
- `node_modules`, `build`, `dist`
- `alembic`, `migrations`

Add custom exclusions via CLI (`--exclude`) or Python API (`excluded_dirs` parameter).

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run linting
ruff check src tests
ruff format src tests

# Run type checking
mypy src

# Run tests
pytest
```

## How It Works

1. **AST Parsing**: Each Python file is parsed into an AST using Python's built-in `ast` module
2. **Import Extraction**: A custom `NodeVisitor` walks the AST to collect all import statements
3. **Definition Extraction**: The same visitor collects all top-level definitions (classes, functions, variables)
4. **Validation**: Each import is validated against:
   - Local project files and their exported symbols
   - External packages via `importlib`

## Limitations

- Does not detect circular imports (planned for future release)
- Does not analyze dynamic imports (`importlib.import_module()` with variables)
- Relative imports are tracked but resolution depends on project structure

## License

MIT
