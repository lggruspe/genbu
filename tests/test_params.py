"""Test genbu.params."""

import decimal
import typing as t

from hypothesis import given, strategies as st
import pytest

from genbu import Param, InvalidOption
from genbu.params import default_aggregator


@pytest.mark.parametrize("dest,optargs", [
    ("foo", ["--foo=bar"]),
    ("bar", ["--bar baz"]),
])
def test_param_with_invalid_option(dest: str, optargs: t.List[str]) -> None:
    """Param should raise InvalidOption if option dest has = or whitespace."""
    with pytest.raises(InvalidOption):
        Param(dest=dest, optargs=optargs)
    assert Param(dest=dest)


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
