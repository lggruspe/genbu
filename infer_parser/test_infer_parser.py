"""Test infer_parser."""
import math
import typing as t
import pytest
from infer_parser import make_parser


def test_make_parser_for_bool() -> None:
    """Test make_parser(bool)."""
    parse = make_parser(bool)
    truthy = (
        ["1"],
        ["t"],
        ["true"],
        ["y"],
        ["yes"],
    )
    falsy = (
        ["0"],
        ["f"],
        ["false"],
        ["n"],
        ["no"],
    )
    invalid: tuple[list[str], ...] = (
        [],
        [""],
        [" false "],
        [" t.r.u.e."],
        ["true", "false"],
    )

    assert all(map(parse, truthy))
    assert not any(map(parse, falsy))
    for tokens in invalid:
        with pytest.raises(ValueError):
            parse(tokens)


def test_make_parser_for_none() -> None:
    """Test make_parser(None)."""
    parse = make_parser(None)
    assert parse([""]) is None
    assert parse(["none"]) is None
    assert parse(["None"]) is None

    invalid: tuple[list[str], ...] = (
        [],
        ["none", "None"],
        ["0"],
    )

    for tokens in invalid:
        with pytest.raises(ValueError):
            parse(tokens)


def test_make_parser_for_float() -> None:
    """Test make_parser(float)."""
    parse = make_parser(float)
    assert parse(["1.5"]) == 1.5
    assert parse(["9.0"]) == 9.0
    with pytest.raises(ValueError):
        parse([])
    with pytest.raises(ValueError):
        parse([""])
    with pytest.raises(ValueError):
        parse(["test"])
    with pytest.raises(ValueError):
        parse(["4", "5"])


def test_make_parser_for_int() -> None:
    """Test make_parser(int)."""
    parse = make_parser(int)
    assert parse(["-5"]) == -5
    assert parse(["9002"]) == 9002
    with pytest.raises(ValueError):
        parse(["0.0"])
    with pytest.raises(ValueError):
        parse([])
    with pytest.raises(ValueError):
        parse([""])
    with pytest.raises(ValueError):
        parse(["4", "5"])


def test_make_parser_for_str() -> None:
    """Test make_parser(str)."""
    parse = make_parser(str)
    assert parse([""]) == ""
    assert parse(["hello world"]) == "hello world"

    with pytest.raises(ValueError):
        parse([])
    with pytest.raises(ValueError):
        parse(["", ""])


def test_make_parser_for_class() -> None:
    """Test make_parser on custom classes."""
    class Err:  # pylint: disable=too-few-public-methods
        """Invalid parser."""

    parse = make_parser(Err)
    with pytest.raises(ValueError):
        parse(["hello"])

    class Ok:  # pylint: disable=too-few-public-methods
        """Valid parser."""
        def __init__(self, arg: str):
            self.arg = arg

    parse = make_parser(Ok)
    result = parse(["hello"])
    assert isinstance(result, Ok)
    assert result.arg == "hello"


def test_make_parser_for_optional() -> None:
    """Test make_parser(Optional[...])."""
    parse = make_parser(t.Optional[float])
    assert parse(["1.5"]) == 1.5
    assert parse([""]) is None
    assert parse(["None"]) is None
    assert parse(["5"]) == 5.0

    with pytest.raises(ValueError):
        parse([])
    with pytest.raises(ValueError):
        parse(["0xe"])


def test_make_parser_for_union() -> None:
    """Test make_parser(Union[...]).

    Order of type parameters matters.
    """
    parse = make_parser(t.Union[int, bool])
    assert parse(["false"]) is False
    assert parse(["False"]) is False
    assert parse(["0"]) == 0
    assert parse(["42"]) == 42

    with pytest.raises(ValueError):
        parse([])
    with pytest.raises(ValueError):
        parse([""])
    with pytest.raises(ValueError):
        parse(["e"])
    with pytest.raises(ValueError):
        parse(["true", "true"])

    zero = make_parser(t.Union[bool, int])("0")
    assert zero is False


def test_make_parser_for_annotated() -> None:
    """Test make_parser on Annotated and Final types."""
    assert make_parser(t.Final[int]) == make_parser(int)
    assert make_parser(t.Annotated[bool, None]) == make_parser(bool)
    assert make_parser(t.Annotated[str, ...]) == make_parser(str)
    assert make_parser(t.Final[t.Annotated[float, None]]) == make_parser(float)


def test_make_parser_for_fixed_length_tuple() -> None:
    """Test make_parser on fixed-length tuple types."""
    parse = make_parser(tuple[int, float])  # type: ignore
    result = parse(["5", "5"])
    assert isinstance(result, tuple)
    assert isinstance(result[0], int)
    assert isinstance(result[1], float)
    assert result == (5, 5.0)

    with pytest.raises(ValueError):
        parse([])
    with pytest.raises(ValueError):
        parse([""])
    with pytest.raises(ValueError):
        parse(["5"])
    with pytest.raises(ValueError):
        parse(["5.0", "5"])

    assert parse(["0", "1.5"]) == (0, 1.5)

    parse = make_parser(tuple[bool, bool, bool])  # type: ignore
    assert parse(["true", "True", "1"]) == (True, True, True)

    parse = make_parser(tuple[tuple[int, ...]])  # type: ignore
    assert parse(["0", "1", "2"]) == ((0, 1, 2),)


def test_make_parser_for_variable_length_tuple() -> None:
    """Test make_parser on variable-length tuple types."""
    parse = make_parser(tuple[float, ...])  # type: ignore

    assert parse([]) == ()
    with pytest.raises(ValueError):
        parse([""])

    result = parse(["0.0", "1.1", "2.2", "3.3"])
    assert isinstance(result, tuple)
    assert all(isinstance(r, float) for r in result)
    assert result == (0.0, 1.1, 2.2, 3.3)

    parse = make_parser(tuple[int, ...])  # type: ignore
    assert parse(["1", "2", "3"]) == (1, 2, 3)
    with pytest.raises(ValueError):
        parse(["1", "2", "3", "four"])

    parse = make_parser(tuple[tuple[int, float], ...])  # type: ignore
    assert parse(["1", "2", "3", "4"]) == ((1, 2.0), (3, 4.0))
    with pytest.raises(ValueError):
        parse(["1", "2", "3"])

    with pytest.raises(TypeError):
        make_parser(tuple[...])  # type: ignore
    with pytest.raises(TypeError):
        make_parser(tuple[..., int])  # type: ignore
    with pytest.raises(TypeError):
        make_parser(tuple[int, float, ...])  # type: ignore


def test_make_parser_for_list() -> None:
    """Test make_parser(list[...])."""
    with pytest.raises(TypeError):
        make_parser(list[list[int]])
    with pytest.raises(TypeError):
        make_parser(list[tuple[int, ...]])  # type: ignore
    with pytest.raises(TypeError):
        make_parser(list[int, bool])  # type: ignore
    with pytest.raises(TypeError):
        make_parser(list[...])  # type: ignore

    parse = make_parser(list[int])
    assert parse([]) == []
    result = parse(["1", "2", "3"])
    assert all(isinstance(r, int) for r in result)
    assert result == [1, 2, 3]

    with pytest.raises(ValueError):
        parse([""])

    parse = make_parser(list[tuple[str, int]])
    assert parse(["foo", "1", "bar", "2"]) == [("foo", 1), ("bar", 2)]
    assert parse([]) == []

    with pytest.raises(ValueError):
        parse(["foo"])
    with pytest.raises(ValueError):
        parse(["foo", "1", "bar"])
    with pytest.raises(ValueError):
        parse(["foo", "bar"])


def test_make_parser_for_dict() -> None:
    """Test make_parser(dict[...])."""
    parse = make_parser(dict[str, float])
    result = parse(["foo", "1.0", "bar", "2.0"])
    assert result == {"foo": 1.0, "bar": 2.0}

    parse = make_parser(dict[int, int])
    assert parse([]) == {}
    assert parse(["1", "2", "3", "4"]) == {1: 2, 3: 4}
    with pytest.raises(ValueError):
        parse(["1", "2", "3"])
    with pytest.raises(ValueError):
        parse(["", ""])
    with pytest.raises(ValueError):
        parse(["1", "2", "3", "foo"])

    unsupported = [
        dict[bool],  # type: ignore
        dict[int, ...],  # type: ignore
        dict[int, list[int]],
        dict[str, str, str],  # type: ignore
    ]
    for type_ in unsupported:
        with pytest.raises(TypeError):
            make_parser(type_)


def test_make_parser_for_unsupported_type() -> None:
    """make_parser should throw UnsupportedType on unsupported types."""
    unsupported = [
        ...,
        list[list[int]],
        tuple[list[int], int],  # type: ignore
        t.Any,
        t.Callable[..., t.Any],
        t.Literal[0, 1, 2],
    ]
    for type_ in unsupported:
        with pytest.raises(TypeError):
            make_parser(type_)


def test_make_parser_for_nested_type() -> None:
    """Test make_parser on nested types."""
    supported = [
        list[int],
        dict[tuple[str, int], tuple[str, tuple[int, float]]],
        tuple[int, dict[str, str]],  # type: ignore
        tuple[str, ...],  # type: ignore
        tuple[tuple[tuple[str, int]], list[int]],  # type: ignore
    ]
    for type_ in supported:
        make_parser(type_)

    invalid = [
        list[int, float],  # type: ignore
        tuple[...],  # type: ignore
        tuple[str, str, ...],  # type: ignore
    ]
    unsupported = [
        list[list[int]],
        list[t.Literal[0]],
        dict[tuple[str, ...], tuple[int]],  # type: ignore
        t.Callable[..., int],
        t.Literal[True, False],
        tuple[dict[str, str], int],  # type: ignore
        tuple[tuple[int, ...], ...],  # type: ignore
    ]
    for type_ in invalid + unsupported:
        with pytest.raises(TypeError):
            make_parser(type_)


def test_make_parser_length() -> None:
    """Test make_parser result.length."""
    cases = {
        bool: 1,
        dict[tuple[int, str], str]: math.inf,
        int: 1,
        list[str]: math.inf,
        t.Annotated[tuple[str, str, str], None]: 3,  # type: ignore
        t.Final[list[int]]: math.inf,
        t.Optional[tuple[int, float]]: math.inf,  # type: ignore
        tuple[int, ...]: math.inf,  # type: ignore
        tuple[int, str, float]: 3,  # type: ignore
        tuple[int, tuple[int, tuple[int, int]]]: 4,  # type: ignore
    }
    for type_, expected in cases.items():
        assert make_parser(type_).length == expected
