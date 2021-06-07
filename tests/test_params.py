"""Test genbu.params."""

import pytest
from genbu import Param, InvalidOption


@pytest.mark.parametrize("name,optargs", [
    ("foo", ["--foo=bar"]),
    ("bar", ["--bar baz"]),
])
def test_param_with_invalid_option(name: str, optargs: list[str]) -> None:
    """Param should raise InvalidOption if option name has = or whitespace."""
    with pytest.raises(InvalidOption):
        Param(name=name, optargs=optargs)
    assert Param(name=name)
