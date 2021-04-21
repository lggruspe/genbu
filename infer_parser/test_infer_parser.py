"""Test infer_parser.py."""

import typing
from typing import Dict, Final, List, Optional, Tuple, Union
from infer_parser import CantInfer, CantParse, infer, parse_bool, parse_none


def test_parse_none() -> None:
    """parse_none should parse '' and 'None' to None and nothing else."""
    assert parse_none("") is None
    assert parse_none("None") is None
    assert parse_none("none") is not None


def test_parse_bool() -> None:
    """parse_bool should parse only 'true', 'True', '1' to True."""
    truthy = ["true", "True", "1"]
    assert all(map(parse_bool, truthy))

    falsy = ["", "false", "False", "0"]
    assert not any(map(parse_bool, falsy))

    assert isinstance(parse_bool("TRue"), CantParse)
    assert isinstance(parse_bool("false "), CantParse)


def test_infer_none() -> None:
    """infer should return parse_none on None."""
    assert infer(None) is parse_none


def test_infer_bool() -> None:
    """infer should return parse_bool on bool."""
    assert infer(bool) is parse_bool


def test_infer_type() -> None:
    """infer should wrap basic and class types to return CantParse on error."""
    parse_float = infer(float)
    assert parse_float("1.5") == 1.5
    assert parse_float("9.0") == 9.0
    assert isinstance(parse_float("test"), CantParse)

    parse_int = infer(int)
    assert parse_int("-5") == -5
    assert parse_int("9002") == 9002
    assert isinstance(parse_int("0.0"), CantParse)


def test_infer_class_type() -> None:
    """infer should wrap custom types."""
    class Ok:  # pylint: disable=too-few-public-methods
        """Valid parser."""
        def __init__(self, arg: str):
            pass

    class Err:  # pylint: disable=too-few-public-methods
        """Invalid parser."""

    ok_ = infer(Ok)
    err = infer(Err)
    assert isinstance(ok_("test"), Ok)
    assert isinstance(err("test"), CantParse)


def test_infer_optional_type() -> None:
    """infer should work with optional types."""
    parse = infer(Optional[float])
    assert parse("1.5") == 1.5
    assert parse("") is None
    assert parse("None") is None
    assert parse("5") == 5.0


def test_infer_union_type() -> None:
    """infer should work with union types."""
    parse = infer(Union[int, bool])
    assert not parse("")
    assert not parse("false")
    assert not parse("False")
    assert parse("0") == 0
    assert parse("42") == 42
    assert isinstance(parse("e"), CantParse)

    zero = infer(Union[bool, int])("0")
    assert not zero
    assert isinstance(zero, bool)


def test_infer_final_type() -> None:
    """infer should work with final types."""
    parse = infer(Final[int])
    assert parse("17") == 17


def test_infer_annotated_type() -> None:
    """infer should work with annotated types."""
    parse = infer(typing.Annotated[bool, None])
    assert parse("false") is False
    assert parse("True") is True


def test_infer_fixed_length_tuple_type() -> None:
    """infer should work with fixed-length tuple types."""
    parse = infer(tuple[int, float])  # type: ignore
    result = parse("5 5")
    assert isinstance(result, tuple)
    assert isinstance(result[0], int)
    assert isinstance(result[1], float)
    assert result == (5, 5.0)

    assert isinstance(parse("5"), CantParse)
    assert isinstance(parse("5.0 5"), CantParse)
    assert parse("  0  '1.5'   ") == (0, 1.5)

    assert infer(Tuple[bool, bool, bool])("True true 1") == \
        (True, True, True)


def test_infer_variable_length_tuple_type() -> None:
    """infer should work with variable-length tuple types."""
    parse = infer(tuple[float, ...])  # type: ignore
    result = parse("0.0 1.1 2.2 '3.3'")

    assert isinstance(result, tuple)
    assert all(isinstance(r, float) for r in result)
    assert result == (0.0, 1.1, 2.2, 3.3)

    assert infer(Tuple[bool, ...])("true True 1") == (True, True, True)
    assert isinstance(infer(Tuple[int, ...])("1 2 3 four"), CantParse)

    assert isinstance(infer(tuple[...]), CantInfer)  # type: ignore
    assert isinstance(infer(tuple[..., int]), CantInfer)  # type: ignore
    assert isinstance(infer(tuple[int, float, ...]), CantInfer)  # type: ignore


def test_infer_list_type() -> None:
    """infer should work with list types."""
    parse = infer(list[float])
    result = parse("0.0 1.1 2.2 '3.3'")

    assert isinstance(result, list)
    assert all(isinstance(r, float) for r in result)
    assert result == [0.0, 1.1, 2.2, 3.3]

    assert infer(List[bool])("true True 1") == [True, True, True]
    assert isinstance(infer(List[int])("1 2 3 four"), CantParse)

    assert isinstance(infer(list[...]), CantInfer)  # type: ignore
    assert isinstance(infer(list[int, float]), CantInfer)  # type: ignore


def test_infer_dict_type() -> None:
    """infer should work with dict types."""
    parse = infer(dict[str, float])
    result = parse("foo 1.0 bar 2.0")
    assert result == {"foo": 1.0, "bar": 2.0}

    assert infer(Dict[int, int])(" 1  2 '3' 4") == {1: 2, 3: 4}
    assert isinstance(infer(Dict[int, int])("1 2 3"), CantParse)
    assert isinstance(infer(Dict[str, float])("1 2 foo bar"), CantParse)

    assert isinstance(infer(dict[bool]), CantInfer)  # type: ignore
    assert isinstance(infer(dict[int, ...]), CantInfer)  # type: ignore
    assert isinstance(infer(dict[str, str, str]), CantInfer)  # type: ignore


def test_infer_nested_type() -> None:
    """infer should work with nested types."""
    parse = infer(Final[Union[Union[int, bool], Optional[float]]])
    assert parse("19.5") == 19.5
    assert parse("false") is False
    assert parse("None") is None


def test_infer_fail() -> None:
    """infer should return CantInfer on failure."""
    assert isinstance(infer(typing.Any), CantInfer)
    assert isinstance(infer(typing.Callable[..., None]), CantInfer)
    assert isinstance(infer(Optional[typing.Literal[0, 1, 2]]), CantInfer)


def test_infer_fail_call() -> None:
    """CantInfer objects CantParse."""
    parse = infer(typing.Any)
    assert isinstance(parse, CantInfer)
    assert isinstance(parse(""), CantParse)
