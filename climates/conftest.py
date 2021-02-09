# type: ignore
"""Pytest fixtures."""
import pytest
from climates import Climate


@pytest.fixture
def cli():
    """Create Climate object."""
    return Climate("test", description="Test CLI app")


@pytest.fixture
def cmd_foo():
    """Create function to be used as command."""
    def foo(a, /):
        """Foo."""
        return "foo", a
    return foo


@pytest.fixture
def cmd_bar():
    """Create function to be used as command."""
    def bar(a, /, *b):
        """Bar."""
        return "bar", a, b
    return bar


@pytest.fixture
def cmd_baz():
    """Create function to be used as command."""
    def baz(a, /, *b, **c):
        """Baz."""
        return "baz", a, b, c
    return baz
