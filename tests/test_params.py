"""Test genbu.params."""

import typing as t
import pytest
from genbu import Param, InvalidOption
from genbu.params import default_resolver


@pytest.mark.parametrize("name,optargs", [
    ("foo", ["--foo=bar"]),
    ("bar", ["--bar baz"]),
])
def test_param_with_invalid_option(name: str, optargs: t.List[str]) -> None:
    """Param should raise InvalidOption if option name has = or whitespace."""
    with pytest.raises(InvalidOption):
        Param(name=name, optargs=optargs)
    assert Param(name=name)


@pytest.mark.parametrize("first,second", [
    ("a", "b"),
    (1, 2),
    (["1"], {"2"}),
])
def test_default_resolver(first: t.Any, second: t.Any) -> None:
    """default_resolver should return second argument."""
    assert default_resolver(first, second) == second
