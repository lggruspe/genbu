# pylint: disable=missing-function-docstring,no-self-use
"""Test infer_parser."""

import collections
import typing as t

from hypothesis import example, given, strategies as st
import pytest

from infer_parser import CantParse, Parser, make_parser

from . import strategies


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
    invalid: t.Tuple[t.List[str], ...] = (
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


class TestNone:
    """Test make_parser(None) parser."""
    @pytest.fixture(scope="class")
    def parser(self) -> Parser:
        return make_parser(None)

    @given(st.lists(st.text()))
    def test_parser_emits_none_result(self,
                                      parser: Parser,
                                      tokens: t.List[str],
                                      ) -> None:
        result = parser(collections.deque(tokens))
        assert result.value is None
        assert result.empty is False

    @given(st.lists(st.text()))
    def test_parser_does_not_mutate_input(self,
                                          parser: Parser,
                                          tokens: t.List[str],
                                          ) -> None:
        deque = collections.deque(tokens)
        before = tuple(deque)
        parser(deque)
        after = tuple(deque)
        assert before == after


@pytest.mark.parametrize("tokens,expected", [
    (["1.5"], 1.5),
    (["9.0"], 9.0),
    (["4", "5"], 4.0),
])
def test_make_parser_for_float(tokens: t.List[str], expected: float) -> None:
    """Test make_parser(float)."""
    parse = make_parser(float)
    assert parse(collections.deque(tokens)).value == expected


@pytest.mark.parametrize("tokens", [
    [], [""], ["test"],
])
def test_make_parser_for_float_invalid_parse(tokens: t.List[str]) -> None:
    """Test make_parser(float) parser on invalid inputs."""
    parse = make_parser(float)
    with pytest.raises(CantParse):
        parse(collections.deque(tokens))


@pytest.mark.parametrize("tokens,expected", [
    (["-5"], -5),
    (["9002"], 9002),
    (["4", "5"], 4),
])
def test_make_parser_for_int(tokens: t.List[str], expected: int) -> None:
    """Test make_parser(int)."""
    parse = make_parser(int)
    assert parse(collections.deque(tokens)).value == expected


@pytest.mark.parametrize("tokens", [
    ["0.0"], [], [""],
])
def test_make_parser_for_int_invalid_parse(tokens: t.List[str]) -> None:
    """Test make_parser(int) parser on invalid inputs."""
    parse = make_parser(int)
    with pytest.raises(CantParse):
        parse(collections.deque(tokens))


@pytest.mark.parametrize("tokens,expected", [
    ([""], ""),
    (["", ""], ""),
    (["hello world"], "hello world"),
])
def test_make_parser_for_str(tokens: t.List[str], expected: str) -> None:
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
def test_make_parser_for_optional(tokens: t.List[str],
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
def test_make_parser_for_union(tokens: t.List[str],
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
def test_make_parser_for_union_invalid_parse(tokens: t.List[str]) -> None:
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


class TestList:
    """Test make_parser(list[int])."""
    @given(
        strategies.t_lists(int).map(make_parser),
        st.lists(st.integers().map(str)),
        st.lists(st.text()).filter(lambda x: not x or not x[0].isdecimal()),
    )
    def test_parser_emits_valid_prefix(self,
                                       parser: Parser,
                                       tokens: t.List[str],
                                       trail: t.List[str],
                                       ) -> None:
        deque = collections.deque(tokens + trail)
        result = parser(deque)

        assert not result.empty
        assert result.value == [int(t) for t in tokens]
        assert tuple(deque) == tuple(trail)

    @given(
        strategies.t_lists(int).map(make_parser),
        st.lists(st.text(st.characters(blacklist_categories=["Nd"]))),
    )
    @example(make_parser(t.List[int]), [])
    @example(make_parser(t.List[int]), [""])
    def test_parser_does_not_mutate_invalid_input(self,
                                                  parser: Parser,
                                                  tokens: t.List[str],
                                                  ) -> None:
        deque = collections.deque(tokens)
        before = tuple(deque)
        parser(deque)
        after = tuple(deque)
        assert before == after


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


class TestDict:  # pylint: disable=too-few-public-methods
    """Test make_parser on dict types."""
    @given(
        strategies.t_dicts(int, int).map(make_parser),
        st.lists(st.text()).filter(
            lambda x: (
                len(x) < 2 or any(not a.strip().isdecimal() for a in x[:2])
            )
        ),
    )
    def test_parser_on_invalid_input(self,
                                     parser: Parser,
                                     tokens: t.List[str],
                                     ) -> None:
        deque = collections.deque(tokens)
        before = tuple(deque)
        result = parser(deque)
        after = tuple(deque)

        assert before == after  # Does not mutate input
        assert not result.empty
        assert result.value == {}  # Emits {}


class TestUnsupported:
    """Test make_parser on unsupported types."""
    @pytest.fixture(scope="class")
    def hints(self) -> t.Iterable[t.Any]:
        result = [
            (),
            ...,
            dict[bool],  # type: ignore
            dict[int, ...],  # type: ignore
            dict[str, str, str],  # type: ignore
            list[()],  # type: ignore
            list[int, float],  # type: ignore
            list[t.Literal[0]],
            t.Any,
            t.Callable[[int], int],
            t.Literal[0],
            t.Tuple[()],
            tuple[(), ()],  # type: ignore
            tuple[()],  # type: ignore
            tuple[...],  # type: ignore
            tuple[str, str, ...],  # type: ignore
        ]
        return result

    def test_make_parser_raises_error(self, hints: t.Iterable[t.Any]) -> None:
        for hint in hints:
            with pytest.raises(TypeError):
                make_parser(hint)


class TestNested:
    """Test make_parser on types with args."""
    @pytest.fixture
    def hints(self) -> t.Iterable[t.Any]:
        return [
            dict[tuple[str, int], tuple[str, tuple[int, float]]],
            list[int],
            tuple[int, dict[str, str]],  # type: ignore
            tuple[str, ...],  # type: ignore
            tuple[tuple[tuple[str, int]], list[int]],  # type: ignore
        ]

    def test_make_parser(self, hints: t.Iterable[t.Any]) -> None:
        for hint in hints:
            make_parser(hint)
        assert True


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


class TestOptionalSequence:
    """Test make_parser on optional sequence types."""
    @given(
        strategies.t_sequences(float).map(
            lambda s: make_parser(t.Optional[s]),
        ),
        st.lists(st.floats(allow_nan=False).map(str)),
    )
    def test_parser_emits_sequence_of_emits(self,
                                            parser: Parser,
                                            tokens: t.List[str],
                                            ) -> None:
        expected = tuple(float(t) for t in tokens)
        result = parser(collections.deque(tokens))
        assert tuple(result.value) == expected

    @given(
        strategies.t_sequences(int).map(lambda s: make_parser(t.Optional[s])),
        st.lists(st.text()).filter(lambda x: not x or not x[0].isdecimal()),
    )
    def test_parser_emits_empty_sequence_instead_of_none(self,
                                                         parser: Parser,
                                                         tokens: t.List[str],
                                                         ) -> None:
        result = parser(collections.deque(tokens))
        assert not result.empty
        assert result.value in ([], ())


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
