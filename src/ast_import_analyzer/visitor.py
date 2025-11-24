"""AST visitor for extracting imports and module definitions."""

import ast


class ImportsVisitor(ast.NodeVisitor):
    """
    AST visitor to extract imported modules and defined symbols from Python code.

    Attributes:
        imported_modules: Set of imported module paths (dotted notation).
        module_defs: Set of locally defined classes, functions, and variables.
    """

    __slots__ = ("imported_modules", "module_defs")

    def __init__(self) -> None:
        self.imported_modules: set[str] = set()
        self.module_defs: set[str] = set()

    def visit_Import(self, node: ast.Import) -> None:
        """
        Visit an Import node (e.g., `import os`).

        Args:
            node: The Import node to visit.
        """
        for alias in node.names:
            self.imported_modules.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """
        Visit an ImportFrom node (e.g., `from os import path`).

        Handles both absolute and relative imports.

        Args:
            node: The ImportFrom node to visit.
        """
        module = node.module or ""  # Handle relative imports where module is None

        for alias in node.names:
            if alias.name == "*":
                # Star import - just track the module
                if module:
                    self.imported_modules.add(module)
            elif module:
                self.imported_modules.add(f"{module}.{alias.name}")
            else:
                # Relative import with no module (from . import foo)
                self.imported_modules.add(alias.name)

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """
        Visit an Assign node to track variable definitions.

        Args:
            node: The Assign node to visit.
        """
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.module_defs.add(target.id)
            elif isinstance(target, ast.Tuple):
                # Handle tuple unpacking: a, b = 1, 2
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        self.module_defs.add(elt.id)

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """
        Visit a FunctionDef node.

        Args:
            node: The FunctionDef node to visit.
        """
        self.module_defs.add(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """
        Visit an AsyncFunctionDef node.

        Args:
            node: The AsyncFunctionDef node to visit.
        """
        self.module_defs.add(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """
        Visit a ClassDef node.

        Args:
            node: The ClassDef node to visit.
        """
        self.module_defs.add(node.name)
        self.generic_visit(node)
