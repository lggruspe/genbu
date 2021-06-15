"""Test infer_parser."""

import collections
import typing as t
import pytest
from infer_parser import CantParse, make_parser


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
    )

    for tokens in truthy:
        assert parse(collections.deque(tokens)).value is True
    for tokens in falsy:
        assert parse(collections.deque(tokens)).value is False
    for tokens in invalid:
        with pytest.raises(CantParse):
            parse(collections.deque(tokens))


@pytest.mark.parametrize("tokens", [
    [], [""], ["none"], ["foo", "bar"],
])
def test_make_parser_for_none(tokens: list[str]) -> None:
    """Test make_parser(None)."""
    parse = make_parser(None)
    deque = collections.deque(tokens)
    before = len(deque)
    result = parse(deque)
    after = len(deque)

    assert before == after
    assert result.value is None
    assert result.empty is False


@pytest.mark.parametrize("tokens,expected", [
    (["1.5"], 1.5),
    (["9.0"], 9.0),
    (["4", "5"], 4.0),
])
def test_make_parser_for_float(tokens: list[str], expected: float) -> None:
    """Test make_parser(float)."""
    parse = make_parser(float)
    assert parse(collections.deque(tokens)).value == expected


@pytest.mark.parametrize("tokens", [
    [], [""], ["test"],
])
def test_make_parser_for_float_invalid_parse(tokens: list[str]) -> None:
    """Test make_parser(float) parser on invalid inputs."""
    parse = make_parser(float)
    with pytest.raises(CantParse):
        parse(collections.deque(tokens))


@pytest.mark.parametrize("tokens,expected", [
    (["-5"], -5),
    (["9002"], 9002),
    (["4", "5"], 4),
])
def test_make_parser_for_int(tokens: list[str], expected: int) -> None:
    """Test make_parser(int)."""
    parse = make_parser(int)
    assert parse(collections.deque(tokens)).value == expected


@pytest.mark.parametrize("tokens", [
    ["0.0"], [], [""],
])
def test_make_parser_for_int_invalid_parse(tokens: list[str]) -> None:
    """Test make_parser(int) parser on invalid inputs."""
    parse = make_parser(int)
    with pytest.raises(CantParse):
        parse(collections.deque(tokens))


@pytest.mark.parametrize("tokens,expected", [
    ([""], ""),
    (["", ""], ""),
    (["hello world"], "hello world"),
])
def test_make_parser_for_str(tokens: list[str], expected: str) -> None:
    """Test make_parser(str)."""
    parse = make_parser(str)
    assert parse(collections.deque(tokens)).value == expected


def test_make_parser_for_str_invalid_parse() -> None:
    """Test make_parser(str)."""
    parse = make_parser(str)
    with pytest.raises(CantParse):
        parse(collections.deque([]))


def test_make_parser_for_class() -> None:
    """Test make_parser on custom classes."""
    class Err:  # pylint: disable=too-few-public-methods
        """Invalid parser."""

    parse = make_parser(Err)
    with pytest.raises(CantParse):
        parse(collections.deque(["hello"]))

    class Ok:  # pylint: disable=too-few-public-methods
        """Valid parser."""
        def __init__(self, arg: str):
            self.arg = arg

    parse = make_parser(Ok)
    result = parse(collections.deque(["hello"])).value
    assert isinstance(result, Ok)
    assert result.arg == "hello"


@pytest.mark.parametrize("tokens,expected", [
    (["1.5"], 1.5),
    ([], None),
    ([""], None),
    (["None"], None),
    (["5", "foo"], 5.0),
    (["5", "6"], 5.0),
    (["0xe"], None),
])
def test_make_parser_for_optional(tokens: list[str],
                                  expected: t.Optional[float],
                                  ) -> None:
    """Test make_parser(Optional[...]).

    It should return None only after it has tried using the other types.
    """
    parse = make_parser(t.Union[float, None])
    assert parse(collections.deque(tokens)).value == expected

    parse = make_parser(t.Union[None, float])
    assert parse(collections.deque(tokens)).value == expected


@pytest.mark.parametrize("tokens,expected", [
    (["false"], False),
    (["False"], False),
    (["0"], 0),
    (["42"], 42),
    (["true", "true"], True),
])
def test_make_parser_for_union(tokens: list[str],
                               expected: t.Union[int, bool],
                               ) -> None:
    """Test make_parser(Union[...]).

    Order of type parameters matters.
    """
    parse = make_parser(t.Union[int, bool])
    assert parse(collections.deque(tokens)).value == expected


@pytest.mark.parametrize("tokens", [
    [], [""], ["e"]
])
def test_make_parser_for_union_invalid_parse(tokens: list[str]) -> None:
    """Test make_parser(Union[...]) on invalid inputs."""
    parse = make_parser(t.Union[int, bool])
    with pytest.raises(CantParse):
        parse(collections.deque(tokens))


def test_make_parser_for_union_order() -> None:
    """MAke sure type hint arguments are checked in order."""
    parse = make_parser(t.Union[bool, int])
    zero = parse(collections.deque(["0"]))
    assert zero.value is False


def test_make_parser_for_annotated() -> None:
    """Test make_parser on Annotated and Final types."""
    assert make_parser(t.Final[int]) == make_parser(int)
    assert make_parser(t.Annotated[bool, None]) == make_parser(bool)
    assert make_parser(t.Annotated[str, ...]) == make_parser(str)
    assert make_parser(t.Final[t.Annotated[float, None]]) == make_parser(float)


def test_make_parser_for_fixed_length_tuple() -> None:
    """Test make_parser on fixed-length tuple types."""
    parse = make_parser(tuple[int, float])  # type: ignore
    result = parse(collections.deque(["5", "5"])).value
    assert isinstance(result, tuple)
    assert isinstance(result[0], int)
    assert isinstance(result[1], float)
    assert result == (5, 5.0)

    invalid: t.Iterable[t.Iterable[str]] = [
        [], [""], ["5"], ["5.0", "5"], ["5", "a"]
    ]
    for tokens in invalid:
        with pytest.raises(CantParse):
            parse(collections.deque(tokens))

    assert parse(collections.deque(["0", "1.5"])).value == (0, 1.5)

    parse = make_parser(tuple[bool, bool, bool])  # type: ignore
    assert parse(collections.deque(["true", "True", "1"])).value == \
        (True, True, True)

    parse = make_parser(tuple[tuple[int, ...]])  # type: ignore
    assert parse(collections.deque(["0", "1", "2"])).value == ((0, 1, 2),)


def test_make_parser_for_variable_length_tuple() -> None:
    """Test make_parser on variable-length tuple types."""
    parse = make_parser(tuple[float, ...])  # type: ignore

    assert parse(collections.deque([])).value == ()
    assert parse(collections.deque([""])).value == ()

    result = parse(collections.deque(["0.0", "1.1", "2.2", "3.3"])).value
    assert isinstance(result, tuple)
    assert all(isinstance(r, float) for r in result)
    assert result == (0.0, 1.1, 2.2, 3.3)

    parse = make_parser(tuple[int, ...])  # type: ignore
    assert parse(collections.deque(["1", "2", "3"])).value == (1, 2, 3)
    assert parse(collections.deque(["1", "2", "3", "four"])).value == (1, 2, 3)

    parse = make_parser(tuple[tuple[int, float], ...])  # type: ignore
    result = parse(collections.deque(["1", "2", "3", "4"]))
    assert result.value == ((1, 2.0), (3, 4.0))
    assert parse(collections.deque(["1", "2", "3"])).value == ((1, 2.0),)

    with pytest.raises(TypeError):
        make_parser(tuple[...])  # type: ignore
    with pytest.raises(TypeError):
        make_parser(tuple[..., int])  # type: ignore
    with pytest.raises(TypeError):
        make_parser(tuple[int, float, ...])  # type: ignore


def test_make_parser_for_list() -> None:
    """Test make_parser(list[...])."""
    parse = make_parser(list[int])
    assert parse(collections.deque([])).value == []
    assert parse(collections.deque([""])).value == []
    result = parse(collections.deque(["1", "2", "3"])).value
    assert result == [1, 2, 3]

    parse = make_parser(list[tuple[str, int]])
    result = parse(collections.deque(["foo", "1", "bar", "2"]))
    assert result.value == [("foo", 1), ("bar", 2)]
    assert parse(collections.deque([])).value == []

    invalid = [
        ["foo"],
        ["foo", "bar"],
    ]
    for tokens in invalid:
        deque = collections.deque(tokens)
        before = len(deque)
        result = parse(deque).value
        after = len(deque)

        assert before == after
        assert result == []


def test_make_parser_for_dict() -> None:
    """Test make_parser(dict[...])."""
    parse = make_parser(dict[str, float])
    result = parse(collections.deque(["foo", "1.0", "bar", "2.0"])).value
    assert result == {"foo": 1.0, "bar": 2.0}

    parse = make_parser(dict[int, int])
    assert parse(collections.deque([])).value == {}
    assert parse(collections.deque(["1", "2", "3", "4"])).value == {1: 2, 3: 4}

    assert parse(collections.deque(["1", "2", "3"])).value == {1: 2}
    assert parse(collections.deque(["1", "2", "3", "foo"])).value == {1: 2}
    assert parse(collections.deque(["", ""])).value == {}

    unsupported = [
        dict[bool],  # type: ignore
        dict[int, ...],  # type: ignore
        dict[str, str, str],  # type: ignore
    ]
    for type_ in unsupported:
        with pytest.raises(TypeError):
            make_parser(type_)


@pytest.mark.parametrize("hint", [
    ...,
    list[int, float],  # type: ignore
    list[t.Literal[0]],
    t.Any,
    t.Callable[[int], int],
    t.Literal[0],
    t.Tuple[()],
    tuple[()],  # type: ignore
    tuple[...],  # type: ignore
    tuple[str, str, ...],  # type: ignore
])
def test_make_parser_for_unsupported_type(hint: t.Any) -> None:
    """make_parser should throw UnsupportedType on unsupported types."""
    with pytest.raises(TypeError):
        make_parser(hint)


@pytest.mark.parametrize("hint", [
    (),
    list[()],  # type: ignore
    t.Tuple[()],
    tuple[(), ()],  # type: ignore
    tuple[()],  # type: ignore
])
def test_make_parser_for_empty_tuple(hint: t.Any) -> None:
    """Test make_parser(...) should fail."""
    with pytest.raises(TypeError):
        make_parser(hint)


@pytest.mark.parametrize("hint", [
    dict[tuple[str, int], tuple[str, tuple[int, float]]],
    list[int],
    tuple[int, dict[str, str]],  # type: ignore
    tuple[str, ...],  # type: ignore
    tuple[tuple[tuple[str, int]], list[int]],  # type: ignore
])
def test_make_parser_for_nested_type(hint: t.Any) -> None:
    """Test make_parser on nested types."""
    make_parser(hint)


def test_make_parser_for_optional_fixed_length_tuple() -> None:
    """Parser should try to parse tuple or return None."""
    parse = make_parser(t.Optional[tuple[int, int]])  # type: ignore

    cases = [
        (["1", "2", "3"], (1, 2)),
        (["1", "2"], (1, 2)),
        (["1"], None),
    ]
    for tokens, expected in cases:
        assert parse(collections.deque(tokens)).value == expected


def test_make_parser_for_optional_list() -> None:
    """Parser should never return None.

    It should return [] instead.
    """
    parse = make_parser(t.Optional[list[int]])

    cases: list[tuple[list[str], list[int]]] = [
        ([], []),
        (["1", "2"], [1, 2]),
        (["1", "2", "3", "a"], [1, 2, 3]),
        (["a", "1"], []),
    ]
    for tokens, expected in cases:
        assert parse(collections.deque(tokens)).value == expected


def test_make_parser_for_dict_with_variable_length_key() -> None:
    """Parser should split keys and values correctly."""
    parse = make_parser(dict[tuple[int, ...], str])  # type: ignore
    cases: t.Any = [
        ([], {}),
        (["a", "b"], {(): "b"}),
        (["1", "2", "a", "b"], {(1, 2): "a", (): "b"}),
    ]
    for tokens, expected in cases:
        assert parse(collections.deque(tokens)).value == expected
