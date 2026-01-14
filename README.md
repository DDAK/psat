<div align="center">

# AST Import Analyzer

**Catch broken Python imports before they crash your production code**

[![PyPI version](https://badge.fury.io/py/ast-import-analyzer.svg)](https://badge.fury.io/py/ast-import-analyzer)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero-brightgreen.svg)](#why-zero-dependencies)

[Features](#features) • [Installation](#installation) • [Quick Start](#quick-start) • [Documentation](#documentation) • [Contributing](#contributing)

</div>

---

## The Problem

You've written Python code. It passes all your tests. You deploy to production. Then:

```python
ImportError: cannot import name 'process_data' from 'app.utils'
```

Someone renamed that function last week. Your IDE didn't catch it. Your tests didn't import that path. **Now your users are seeing 500 errors.**

## The Solution

**AST Import Analyzer** statically analyzes your entire codebase and finds broken imports *before* runtime—without executing a single line of your code.

```bash
$ ast-import-analyzer ./myproject

Import Analysis Report: ./myproject
============================================================
Files analyzed: 127
Issues found: 3
------------------------------------------------------------
[UNDEFINED] app/api/handlers.py: 'app.services.user' does not define 'get_user_by_email'
[UNDEFINED] app/tasks/worker.py: 'app.utils' does not define 'process_data'
[EXTERNAL]  app/integrations/slack.py: Module 'slack_sdk' is not installed
```

**Three bugs caught. Zero runtime errors. Zero dependencies installed.**

---

## Features

| Feature | Description |
|---------|-------------|
| **Dangling Import Detection** | Find imports referencing non-existent modules |
| **Missing Attribute Detection** | Catch imports of undefined functions, classes, or variables |
| **External Package Validation** | Verify that imported packages are actually installed |
| **Smart Directory Exclusion** | Auto-skips `venv`, `__pycache__`, `node_modules`, etc. |
| **Virtual Environment Aware** | Detects and ignores virtual environment directories |
| **Zero Dependencies** | Pure Python—just `pip install` and go |
| **Blazing Fast** | Single-pass AST analysis, handles large codebases efficiently |

---

## Installation

```bash
pip install ast-import-analyzer
```

Or install from source:

```bash
git clone https://github.com/ddak/ast-import-analyzer.git
cd ast-import-analyzer
pip install -e .
```

---

## Quick Start

Analyze your project in one command:

```bash
ast-import-analyzer /path/to/your/project
```

That's it. No configuration files. No setup. Just answers.

### Common Options

```bash
# Verbose output (see every file being analyzed)
ast-import-analyzer ./src -v

# Exclude specific directories
ast-import-analyzer ./src --exclude tests fixtures migrations

# Auto-fix with ruff before analysis
ast-import-analyzer ./src --fix
```

---

## Documentation

### Python API

For programmatic access or CI/CD integration:

```python
from ast_import_analyzer import LinterManager

# Analyze your project
manager = LinterManager("/path/to/project")
issues = manager.run()

# Fail CI if issues found
if issues:
    for issue in issues:
        print(f"{issue.issue_type}: {issue.file}")
        print(f"  → {issue.message}")
    exit(1)
```

### Single File Analysis

```python
from pathlib import Path
from ast_import_analyzer import PythonFileAnalyzer

analyzer = PythonFileAnalyzer(Path("mymodule.py"))
analyzer.analyze()

print(f"Imports: {analyzer.imported_modules}")
print(f"Exports: {analyzer.module_defs}")
```

### Issue Types

| Type | Meaning |
|------|---------|
| `UNDEFINED` | Import references something not defined in the target module |
| `EXTERNAL` | External package is not installed or doesn't have the requested attribute |

---

## Default Exclusions

These directories are automatically skipped:

- Build artifacts: `__pycache__`, `build`, `dist`
- Version control: `.git`, `.github`, `.gitlab`
- Virtual environments: `venv`, `.venv`, `env`, `.env`
- Other: `node_modules`, `alembic`, `migrations`

Override with `--exclude` or the `excluded_dirs` parameter in Python.

---

## Why Zero Dependencies?

- **No version conflicts** with your project's dependencies
- **Installs instantly** in any environment
- **Works offline** after installation
- **Minimal attack surface** for security-conscious teams

The entire tool is built on Python's standard library: `ast`, `importlib`, and `pathlib`.

---

## How It Works

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Python File   │────▶│   AST Parser    │────▶│  Import Visitor │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                               ┌─────────────────────────┘
                               ▼
                    ┌─────────────────────┐
                    │  Import Validation  │
                    │  • Local modules    │
                    │  • External packages│
                    └─────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    Issue Report     │
                    └─────────────────────┘
```

1. **Parse**: Each `.py` file is parsed into an AST (no code execution)
2. **Extract**: Custom `NodeVisitor` collects imports and definitions
3. **Validate**: Each import is checked against local files and installed packages
4. **Report**: Issues are categorized and reported with file paths and descriptions

---

## CI/CD Integration

### GitHub Actions

```yaml
- name: Check imports
  run: |
    pip install ast-import-analyzer
    ast-import-analyzer ./src
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: ast-import-analyzer
        name: Check Python imports
        entry: ast-import-analyzer
        language: system
        types: [python]
        args: [./src]
```

---

## Limitations

- **Circular imports**: Not detected (planned for future release)
- **Dynamic imports**: `importlib.import_module(var)` with variable paths not analyzed
- **Conditional imports**: Imports inside `if TYPE_CHECKING:` are still validated

---

## Development

```bash
# Clone and install with dev dependencies
git clone https://github.com/ddak/ast-import-analyzer.git
cd ast-import-analyzer
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check src tests
mypy src
```

---

## Contributing

Contributions are welcome! Whether it's:

- Bug reports
- Feature requests
- Documentation improvements
- Code contributions

Please feel free to open an issue or submit a PR.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

**If this tool saved you from a production bug, consider giving it a star!**

[Report Bug](https://github.com/ddak/ast-import-analyzer/issues) • [Request Feature](https://github.com/ddak/ast-import-analyzer/issues)

</div>
