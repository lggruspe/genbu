# pylint: disable=missing-function-docstring,unused-argument
"""Test infer_params.py."""

import platform
import typing as t

from hypothesis import given, strategies as st
import pytest

from genbu.infer_params import (
    UnsupportedCallback, infer_params_from_signature as infer
)


def test_infer_treats_unannotated_parameter_as_str() -> None:
    def function(arg):  # type: ignore
        """Does nothing."""

    params = infer(function)
    assert len(params) == 1

    param = params[0]
    assert param.dest == "arg"
    assert param.optargs == ["--arg"]
    assert str(param.parser) == "str"


def test_infer_treats_var_positional_arg_as_tuple() -> None:
    def function(*args: complex) -> None:
        """Does nothing."""

    params = infer(function)
    assert len(params) == 1

    param = params[0]
    assert param.dest == "args"
    assert param.optargs == ["--args"]
    assert str(param.parser) == "[complex...]"


def test_infer_treats_var_keyword_arg_as_dict() -> None:
    def function(**kwargs: int) -> None:
        """Does nothing."""

    params = infer(function)
    assert len(params) == 1

    param = params[0]
    assert param.dest == "kwargs"
    assert param.optargs == ["--kwargs"]
    assert str(param.parser) == "[(str int)...]"


@given(st.from_type(object).filter(lambda x: not callable(x)))
def test_infer_raises_unsupported_callback_if_not_callable(func: t.Any,
                                                           ) -> None:
    with pytest.raises(UnsupportedCallback) as info:
        infer(func)
    assert info.type is UnsupportedCallback
    assert info.value.callback is func


@pytest.mark.skipif(platform.python_implementation() != "CPython",
                    reason="for CPython")
@pytest.mark.parametrize("func", [str, int, print])
def test_infer_raises_unsupported_callback_if_it_has_no_signature(func: t.Any,
                                                                  ) -> None:
    with pytest.raises(UnsupportedCallback) as info:
        infer(func)
    assert info.type is UnsupportedCallback
    assert info.value.callback is func
