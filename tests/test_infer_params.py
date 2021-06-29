# pylint: disable=missing-function-docstring,unused-argument
"""Test infer_params.py."""

from genbu.infer_params import infer_params_from_signature as infer


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
