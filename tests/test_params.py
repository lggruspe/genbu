"""Test genbu.params."""

import decimal
import typing as t

from hypothesis import given, strategies as st
import pytest

from genbu import Param, InvalidOption
from genbu.params import default_aggregator


@pytest.mark.parametrize("name,optargs", [
    ("foo", ["--foo=bar"]),
    ("bar", ["--bar baz"]),
])
def test_param_with_invalid_option(name: str, optargs: t.List[str]) -> None:
    """Param should raise InvalidOption if option name has = or whitespace."""
    with pytest.raises(InvalidOption):
        Param(name=name, optargs=optargs)
    assert Param(name=name)


@given(
    st.lists(
        st.from_type(object).filter(
            lambda x: type(x) not in (complex, float, decimal.Decimal),
        ),
        min_size=1,
    ),
)
def test_default_aggregator(lst: t.List[t.Any]) -> None:
    """default_aggregator should return last element."""
    assert default_aggregator(lst) == lst[-1]
