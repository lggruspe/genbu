# pylint: disable=missing-function-docstring,no-self-use,unsubscriptable-object
"""Test infer_parser."""

import collections
import sys
import typing as t

from hypothesis import example, given, strategies as st
import pytest

from genbu import CantParse
from genbu.combinators import Parser
from genbu.infer import infer_parser

from . import strategies


def test_make_parser_for_bool() -> None:
    """Test infer_parser(bool)."""
    parse = infer_parser(bool)
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
    """Test infer_parser(None) parser."""
    @pytest.fixture(scope="class")
    def parser(self) -> Parser:
        return infer_parser(None)

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
    """Test infer_parser(float)."""
    parse = infer_parser(float)
    assert parse(collections.deque(tokens)).value == expected


@pytest.mark.parametrize("tokens", [
    [], [""], ["test"],
])
def test_make_parser_for_float_invalid_parse(tokens: t.List[str]) -> None:
    """Test infer_parser(float) parser on invalid inputs."""
    parse = infer_parser(float)
    with pytest.raises(CantParse):
        parse(collections.deque(tokens))


@pytest.mark.parametrize("tokens,expected", [
    (["-5"], -5),
    (["9002"], 9002),
    (["4", "5"], 4),
])
def test_make_parser_for_int(tokens: t.List[str], expected: int) -> None:
    """Test infer_parser(int)."""
    parse = infer_parser(int)
    assert parse(collections.deque(tokens)).value == expected


@pytest.mark.parametrize("tokens", [
    ["0.0"], [], [""],
])
def test_make_parser_for_int_invalid_parse(tokens: t.List[str]) -> None:
    """Test infer_parser(int) parser on invalid inputs."""
    parse = infer_parser(int)
    with pytest.raises(CantParse):
        parse(collections.deque(tokens))


@pytest.mark.parametrize("tokens,expected", [
    ([""], ""),
    (["", ""], ""),
    (["hello world"], "hello world"),
])
def test_make_parser_for_str(tokens: t.List[str], expected: str) -> None:
    """Test infer_parser(str)."""
    parse = infer_parser(str)
    assert parse(collections.deque(tokens)).value == expected


def test_make_parser_for_str_invalid_parse() -> None:
    """Test infer_parser(str)."""
    parse = infer_parser(str)
    with pytest.raises(CantParse):
        parse(collections.deque([]))


def test_make_parser_for_class() -> None:
    """Test infer_parser on custom classes."""
    class Err:  # pylint: disable=too-few-public-methods
        """Invalid parser."""

    parse = infer_parser(Err)
    with pytest.raises(CantParse):
        parse(collections.deque(["hello"]))

    class Ok:  # pylint: disable=too-few-public-methods
        """Valid parser."""
        def __init__(self, arg: str):
            self.arg = arg

    parse = infer_parser(Ok)
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
    """Test infer_parser(Optional[...]).

    It should return None only after it has tried using the other types.
    """
    parse = infer_parser(t.Union[float, None])
    assert parse(collections.deque(tokens)).value == expected

    parse = infer_parser(t.Union[None, float])
    assert parse(collections.deque(tokens)).value == expected


@pytest.mark.parametrize("tokens,expected", [
    (["false"], False),
    (["False"], False),
    (["0"], 0),
    (["42.1"], 42.1),
    (["true", "true"], True),
])
def test_make_parser_for_union(tokens: t.List[str],
                               expected: t.Union[float, bool],
                               ) -> None:
    """Test infer_parser(Union[...]).

    Order of type parameters matters.
    """
    parse = infer_parser(t.Union[float, bool])
    assert parse(collections.deque(tokens)).value == expected


@pytest.mark.parametrize("tokens", [
    [], [""], ["e"]
])
def test_make_parser_for_union_invalid_parse(tokens: t.List[str]) -> None:
    """Test infer_parser(Union[...]) on invalid inputs."""
    parse = infer_parser(t.Union[float, bool])
    with pytest.raises(CantParse):
        parse(collections.deque(tokens))


def test_make_parser_for_union_order() -> None:
    """Make sure type hint arguments are checked in order.

    Note: t.Union[bool, int] becomes int in python 3.6.
    """
    parse = infer_parser(t.Union[bool, float])
    zero = parse(collections.deque(["0"]))
    assert zero.value is False


@pytest.mark.skipif(sys.version_info < (3, 9), reason="requires python 3.9")
@pytest.mark.parametrize("args", [(bool, None), (str, ...)])
def test_make_parser_for_annotated(args: t.Any) -> None:
    """Test infer_parser on Annotated types."""
    annotated = getattr(t, "Annotated")
    assert infer_parser(annotated[args]) == infer_parser(args[0])


@pytest.mark.skipif(sys.version_info < (3, 8), reason="requires python 3.8")
def test_make_parser_for_final() -> None:
    """Test make parser on Final types."""
    final = getattr(t, "Final")  # pylint: disable=no-member
    assert infer_parser(final[int]) == infer_parser(int)


@pytest.mark.parametrize("typ", [int, float, str])
def test_make_parser_for_type(typ: type) -> None:
    """Test infer_parser on Type[...]."""
    assert infer_parser(t.Type[typ]) == infer_parser(typ)


class TestFixedLengthTuple:
    """Test infer_parser(tuple[int, float])."""
    @given(
        strategies.t_tuples(int, float).map(infer_parser),
        st.from_type(t.Tuple[int, float]).map(  # type: ignore
            lambda x: list(map(str, x))
        ).filter(lambda x: x[-1] != "nan"),
    )
    def test_parser_parses_to_correct_type(self,
                                           parser: Parser,
                                           tokens: t.List[str],
                                           ) -> None:
        """Test infer_parser on fixed-length tuple types."""
        result = parser(collections.deque(tokens)).value
        assert isinstance(result, tuple)
        assert result == (int(tokens[0]), float(tokens[1]))

        first, second = result
        assert isinstance(first, int)
        assert isinstance(second, float)

    @given(strategies.t_tuples(int, float).map(infer_parser))
    def test_parser_on_invalid_input(self, parser: Parser) -> None:
        invalid: t.Iterable[t.Iterable[str]] = [
            [], [""], ["5"], ["5.0", "5"], ["5", "a"]
        ]
        for tokens in invalid:
            with pytest.raises(CantParse):
                parser(collections.deque(tokens))


class TestVariableLengthTuple:
    """Test infer_parser(tuple[float, ...])."""
    @given(
        strategies.t_tuples(float, ...).map(infer_parser),
    )
    def test_make_parser_for_variable_length_tuple(self,
                                                   parser: Parser,
                                                   ) -> None:
        """Test infer_parser on variable-length tuple types."""
        assert parser(collections.deque([])).value == ()
        assert parser(collections.deque([""])).value == ()

        result = parser(collections.deque(["0.0", "1.1", "2.2", "3.3"])).value
        assert isinstance(result, tuple)
        assert all(isinstance(r, float) for r in result)
        assert result == (0.0, 1.1, 2.2, 3.3)

    @given(
        strategies.t_tuples(int, ...).map(infer_parser),
        st.lists(st.integers().map(str)),
        st.lists(st.text()).filter(
            lambda x: not x or not x[0].strip().isdecimal()
        ),
    )
    def test_parser_consumes_prefix(self,
                                    parser: Parser,
                                    tokens: t.List[str],
                                    trail: t.List[str],
                                    ) -> None:
        deque = collections.deque(tokens + trail)
        result = parser(deque)

        assert result.value == tuple(map(int, tokens))
        assert list(deque) == trail

    @pytest.mark.skipif(sys.version_info < (3, 9),
                        reason="requires python 3.9")
    def test_make_parser_raises_error(self) -> None:
        hints = [
            tuple[...],  # type: ignore
            tuple[..., int],  # type: ignore
            tuple[int, float, ...],  # type: ignore
        ]
        for hint in hints:
            with pytest.raises(TypeError):
                infer_parser(hint)


class TestNestedSequence:
    """Test infer_parser on nested sequence types."""
    def test_make_parser_for_nested_tuple(self) -> None:
        """Parser should parse inner tuple correctly."""
        parser = infer_parser(t.Tuple[t.Tuple[int, float], ...])
        result = parser(collections.deque(["1", "2", "3", "4"]))
        assert result.value == ((1, 2.0), (3, 4.0))
        assert parser(collections.deque(["1", "2", "3"])).value == ((1, 2.0),)

    @given(
        strategies.t_sequences(int),
        st.lists(st.integers().map(str), min_size=1),
    )
    def test_parser_with_sequence_inside(self,
                                         nested: t.Any,
                                         tokens: t.List[str],
                                         ) -> None:
        """Only the first type arg ever gets used."""
        parser = infer_parser(t.List[nested])  # type: ignore
        value = parser(collections.deque(tokens)).value
        assert len(value) == 1
        assert list(value[0]) == [int(t) for t in tokens]


class TestList:
    """Test infer_parser(list[int])."""
    @given(
        strategies.t_lists(int).map(infer_parser),
        st.lists(st.integers().map(str)),
        st.lists(st.text()).filter(
            lambda x: not x or not x[0].strip().isdecimal(),
        ),
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
        strategies.t_lists(int).map(infer_parser),
        st.lists(st.text(st.characters(blacklist_categories=["Nd"]))),
    )
    @example(infer_parser(t.List[int]), [])
    @example(infer_parser(t.List[int]), [""])
    def test_parser_does_not_mutate_invalid_input(self,
                                                  parser: Parser,
                                                  tokens: t.List[str],
                                                  ) -> None:
        deque = collections.deque(tokens)
        before = tuple(deque)
        parser(deque)
        after = tuple(deque)
        assert before == after


class TestDict:  # pylint: disable=too-few-public-methods
    """Test infer_parser on dict types."""
    @given(
        strategies.t_dicts(int, int).map(infer_parser),
        st.lists(st.integers().map(str)).filter(lambda x: len(x) % 2 != 0),
    )
    def test_parser_ignores_incomplete_key_value_pair(self,
                                                      parser: Parser,
                                                      tokens: t.List[str],
                                                      ) -> None:
        expected = {int(a): int(b) for a, b in zip(tokens[::2], tokens[1::2])}
        deque = collections.deque(tokens)
        result = parser(deque)
        assert result.value == expected
        assert list(deque) == tokens[-1:]

    @given(
        strategies.t_dicts(int, int).map(infer_parser),
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
    """Test infer_parser on unsupported types."""
    @pytest.fixture(scope="class")
    def generic_aliases(self) -> t.Iterable[t.Any]:
        return [
            dict[bool],  # type: ignore
            dict[int, ...],  # type: ignore
            dict[str, str, str],  # type: ignore
            list[()],  # type: ignore
            list[int, float],  # type: ignore
            tuple[(), ()],  # type: ignore
            tuple[...],  # type: ignore
            tuple[str, str, ...],  # type: ignore
        ]

    @pytest.mark.skipif(sys.version_info < (3, 9), reason="needs python 3.9")
    def test_make_parser_raises_error_on_invalid_generic_alias(
        self,
        generic_aliases: t.Iterable[t.Any],
    ) -> None:
        for hint in generic_aliases:
            with pytest.raises(TypeError):
                infer_parser(hint)

    def test_make_parser_raises_error_on_unsupported_types(self) -> None:
        hints = [
            (),
            ...,
            t.Any,
            t.Callable[[int], int],
        ]
        for hint in hints:
            with pytest.raises(TypeError):
                infer_parser(hint)


class TestNested:
    """Test infer_parser on types with args."""
    def test_nested_types(self) -> None:
        hints = [
            t.Dict[t.Tuple[str, int], t.Tuple[str, t.Tuple[int, float]]],
            t.List[int],
            t.Tuple[int, t.Dict[str, str]],
            t.Tuple[str, ...],
            t.Tuple[t.Tuple[t.Tuple[str, int]], t.List[int]],
        ]
        for hint in hints:
            infer_parser(hint)
        assert True

    @pytest.mark.skipif(sys.version_info < (3, 9), reason="needs python 3.9")
    def test_nested_generic_aliases(self) -> None:
        hints = [
            dict[  # type: ignore
                tuple[str, int], tuple[str, tuple[int, float]]  # type: ignore
            ],
            list[int],  # type: ignore
            tuple[int, dict[str, str]],  # type: ignore
            tuple[str, ...],  # type: ignore
            tuple[tuple[tuple[str, int]], list[int]],  # type: ignore
        ]
        for hint in hints:
            infer_parser(hint)
        assert True


def test_make_parser_for_optional_fixed_length_tuple() -> None:
    """Parser should try to parse tuple or return None."""
    parse = infer_parser(t.Optional[t.Tuple[int, int]])

    cases = [
        (["1", "2", "3"], (1, 2)),
        (["1", "2"], (1, 2)),
        (["1"], None),
    ]
    for tokens, expected in cases:
        assert parse(collections.deque(tokens)).value == expected


class TestOptionalSequence:
    """Test infer_parser on optional sequence types."""
    @given(
        strategies.t_sequences(float).map(
            lambda s: infer_parser(t.Optional[s]),
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
        strategies.t_sequences(int).map(lambda s: infer_parser(t.Optional[s])),
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
    parse = infer_parser(t.Dict[t.Tuple[int, ...], str])
    cases: t.Any = [
        ([], {}),
        (["a", "b"], {(): "b"}),
        (["1", "2", "a", "b"], {(1, 2): "a", (): "b"}),
    ]
    for tokens, expected in cases:
        assert parse(collections.deque(tokens)).value == expected


@pytest.mark.skipif(sys.version_info < (3, 8), reason="requires python 3.8")
class TestLiteral:
    """Test infer_parser on t.Literal[...]."""
    @pytest.mark.parametrize("integer", list(range(10)))
    def test_parser_on_valid_int_literals(self, integer: int) -> None:
        literal = getattr(t, "Literal")  # pylint: disable=no-member
        parser = infer_parser(literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        result = parser(collections.deque([str(integer)]))
        assert result.value == integer

    @given(st.integers().filter(lambda x: x < 0 or x > 9))
    def test_parser_on_invalid_int_literals(self, integer: int) -> None:
        literal = getattr(t, "Literal")  # pylint: disable=no-member
        parser = infer_parser(literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        with pytest.raises(CantParse):
            parser(collections.deque([str(integer)]))


@given(
    strategies.t_tuples(()),
    st.lists(st.text()),
)
def test_empty_tuple(hint: t.Any, tokens: t.List[str]) -> None:
    """Parser should emit () without modifying the input."""
    parser = infer_parser(hint)
    deque = collections.deque(tokens)
    before = list(deque)
    result = parser(deque)
    after = list(deque)

    assert before == after
    assert not result.empty
    assert result.value == ()
