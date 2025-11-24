"""Tests for the ImportsVisitor class."""

import ast

import pytest

from ast_import_analyzer.visitor import ImportsVisitor


class TestImportsVisitor:
    """Test suite for ImportsVisitor."""

    def test_simple_import(self):
        """Test detection of simple import statements."""
        code = "import os"
        tree = ast.parse(code)
        visitor = ImportsVisitor()
        visitor.visit(tree)

        assert "os" in visitor.imported_modules

    def test_multiple_imports(self):
        """Test detection of multiple imports on one line."""
        code = "import os, sys, json"
        tree = ast.parse(code)
        visitor = ImportsVisitor()
        visitor.visit(tree)

        assert "os" in visitor.imported_modules
        assert "sys" in visitor.imported_modules
        assert "json" in visitor.imported_modules

    def test_from_import(self):
        """Test detection of from...import statements."""
        code = "from os import path"
        tree = ast.parse(code)
        visitor = ImportsVisitor()
        visitor.visit(tree)

        assert "os.path" in visitor.imported_modules

    def test_from_import_multiple(self):
        """Test detection of multiple names in from...import."""
        code = "from os import path, getcwd, listdir"
        tree = ast.parse(code)
        visitor = ImportsVisitor()
        visitor.visit(tree)

        assert "os.path" in visitor.imported_modules
        assert "os.getcwd" in visitor.imported_modules
        assert "os.listdir" in visitor.imported_modules

    def test_nested_from_import(self):
        """Test detection of nested module imports."""
        code = "from os.path import join, dirname"
        tree = ast.parse(code)
        visitor = ImportsVisitor()
        visitor.visit(tree)

        assert "os.path.join" in visitor.imported_modules
        assert "os.path.dirname" in visitor.imported_modules

    def test_relative_import_with_module(self):
        """Test detection of relative imports with module name."""
        code = "from .utils import helper"
        tree = ast.parse(code)
        visitor = ImportsVisitor()
        visitor.visit(tree)

        assert "utils.helper" in visitor.imported_modules

    def test_relative_import_no_module(self):
        """Test detection of relative imports without module name."""
        code = "from . import config"
        tree = ast.parse(code)
        visitor = ImportsVisitor()
        visitor.visit(tree)

        assert "config" in visitor.imported_modules

    def test_star_import(self):
        """Test detection of star imports."""
        code = "from os import *"
        tree = ast.parse(code)
        visitor = ImportsVisitor()
        visitor.visit(tree)

        assert "os" in visitor.imported_modules

    def test_function_definition(self):
        """Test detection of function definitions."""
        code = """
def my_function():
    pass
"""
        tree = ast.parse(code)
        visitor = ImportsVisitor()
        visitor.visit(tree)

        assert "my_function" in visitor.module_defs

    def test_async_function_definition(self):
        """Test detection of async function definitions."""
        code = """
async def my_async_function():
    pass
"""
        tree = ast.parse(code)
        visitor = ImportsVisitor()
        visitor.visit(tree)

        assert "my_async_function" in visitor.module_defs

    def test_class_definition(self):
        """Test detection of class definitions."""
        code = """
class MyClass:
    pass
"""
        tree = ast.parse(code)
        visitor = ImportsVisitor()
        visitor.visit(tree)

        assert "MyClass" in visitor.module_defs

    def test_variable_assignment(self):
        """Test detection of variable assignments."""
        code = "MY_CONSTANT = 42"
        tree = ast.parse(code)
        visitor = ImportsVisitor()
        visitor.visit(tree)

        assert "MY_CONSTANT" in visitor.module_defs

    def test_tuple_unpacking(self):
        """Test detection of tuple unpacking assignments."""
        code = "a, b, c = 1, 2, 3"
        tree = ast.parse(code)
        visitor = ImportsVisitor()
        visitor.visit(tree)

        assert "a" in visitor.module_defs
        assert "b" in visitor.module_defs
        assert "c" in visitor.module_defs

    def test_nested_class_detection(self):
        """Test that nested classes are detected via generic_visit."""
        code = """
class Outer:
    class Inner:
        pass
"""
        tree = ast.parse(code)
        visitor = ImportsVisitor()
        visitor.visit(tree)

        assert "Outer" in visitor.module_defs
        assert "Inner" in visitor.module_defs

    def test_nested_function_in_class(self):
        """Test that methods in classes are detected."""
        code = """
class MyClass:
    def my_method(self):
        pass
"""
        tree = ast.parse(code)
        visitor = ImportsVisitor()
        visitor.visit(tree)

        assert "MyClass" in visitor.module_defs
        assert "my_method" in visitor.module_defs

    def test_complex_file(self):
        """Test a complex file with multiple imports and definitions."""
        code = """
import os
import sys
from pathlib import Path
from typing import Optional, List

MY_VAR = "test"

class Config:
    DEBUG = True

def get_config():
    return Config()

async def async_loader():
    pass
"""
        tree = ast.parse(code)
        visitor = ImportsVisitor()
        visitor.visit(tree)

        # Check imports
        assert "os" in visitor.imported_modules
        assert "sys" in visitor.imported_modules
        assert "pathlib.Path" in visitor.imported_modules
        assert "typing.Optional" in visitor.imported_modules
        assert "typing.List" in visitor.imported_modules

        # Check definitions
        assert "MY_VAR" in visitor.module_defs
        assert "Config" in visitor.module_defs
        assert "get_config" in visitor.module_defs
        assert "async_loader" in visitor.module_defs

    def test_empty_file(self):
        """Test parsing an empty file."""
        code = ""
        tree = ast.parse(code)
        visitor = ImportsVisitor()
        visitor.visit(tree)

        assert len(visitor.imported_modules) == 0
        assert len(visitor.module_defs) == 0
