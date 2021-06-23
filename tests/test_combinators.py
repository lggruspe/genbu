"""Test arg parser combinators."""

import collections
import shlex
import typing as t

from hypothesis import given, strategies as st
import pytest

from genbu import combinators as comb


def as_tokens(source: t.Union[str, t.Iterable[str]]) -> comb.Tokens:
    """Convert source into Tokens."""
    if isinstance(source, str):
        source = shlex.split(source)
    return collections.deque(source)


@pytest.mark.parametrize("parse,source,expected", [
    (comb.One(int), "50", 50),
    (comb.One(int), "-123 2", -123),
    (comb.One(float), "-123.2", -123.2),
    (comb.One(str), "hello", "hello"),
])
def test_one_parse_valid(parse: comb.Parser,
                         source: str,
                         expected: int,
                         ) -> None:
    """One(f) parser must consume one f from the input."""
    assert parse(as_tokens(source)).value == expected


@pytest.mark.parametrize("parse,source", [
    (comb.One(int), []),
    (comb.One(int), ["1.1"]),
    (comb.One(int), ["a"]),
])
def test_one_parse_invalid(parse: comb.Parser,
                           source: t.Iterable[str],
                           ) -> None:
    """One(f) parser must raise CantParse."""
    with pytest.raises(comb.CantParse):
        parse(as_tokens(source))


@pytest.mark.parametrize("source,expected", [
    ("123456", 123456),
    ("123.4 123123", 123.4),
    ("foo bar", "foo"),
])
def test_or_parse_valid(source: str, expected: t.Any) -> None:
    """Or(f, g, ...) parser should match first valid input."""
    parse = comb.Or(comb.One(int), comb.One(float), comb.One(str))
    assert parse(as_tokens(source)).value == expected


@pytest.mark.parametrize("source,parse", [
    ("hello", comb.Or()),
    ("1.5", comb.Or(comb.One(int))),
    ("a", comb.Or(comb.One(int), comb.One(float))),
])
def test_or_parse_invalid(source: str, parse: comb.Parser) -> None:
    """Or(f, g, ...) parser should raise CantParse."""
    with pytest.raises(comb.CantParse):
        parse(as_tokens(source))


@pytest.mark.parametrize("source,expected,parse", [
    ("foo bar baz", {}, comb.And(then=dict)),
    ("1 1.5 hello", [1, 1.5, "hello"], comb.And(
        comb.One(int), comb.One(float), comb.One(str), then=list
    )),
    ("5 5 5", ("5", 5.0, 5), comb.And(
        comb.One(str), comb.One(float), comb.One(int), then=tuple
    )),
])
def test_and_parse_valid(source: str,
                         expected: t.Any,
                         parse: comb.Parser,
                         ) -> None:
    """And(f, g, ...) parser should parse space separated list."""
    assert parse(as_tokens(source)).value == expected


@pytest.mark.parametrize("source,parse", [
    ("1.5", comb.And(comb.One(int))),
    ("hello 5.6", comb.And(comb.One(str), comb.One(int))),
])
def test_and_parse_invalid(source: str, parse: comb.Parser) -> None:
    """And(f, g, ...) parser should raise CantParse."""
    with pytest.raises(comb.CantParse):
        parse(as_tokens(source))


@pytest.mark.parametrize("source,expected,parse", [
    ("", [], comb.Repeat(comb.One(float), then=list)),
    ("ok", (), comb.Repeat(comb.One(float), then=tuple)),
    ("5 5 5 5 stop", 20, comb.Repeat(comb.One(int), then=sum)),
])
def test_repeat_parse_valid(source: str,
                            expected: t.Any,
                            parse: comb.Parser,
                            ) -> None:
    """Repeat(p) parser should run p parser as many times as needed."""
    assert parse(as_tokens(source)).value == expected


@pytest.mark.parametrize("source,parse", [
    ("a", comb.Repeat(comb.One(int))),
    ("1.5", comb.Repeat(comb.One(int))),
])
def test_repeat_parse_invalid(source: str, parse: comb.Parser) -> None:
    """Repeat(p) parser should not modify input tokens."""
    tokens = as_tokens(source)
    before = tuple(tokens)

    result = parse(as_tokens(source))
    assert result.value == []
    assert not result.empty

    after = tuple(tokens)
    assert before == after


def test_repeat_parse_infinite() -> None:
    """Repeat(p) parser should break out of infinite loop.

    Ex: Emit always parses successfully, so Repeat(Emit(...)) would keep
    parsing forever if it doesn't break out of the loop.
    """
    parse = comb.Repeat(comb.Emit(True))

    tokens = as_tokens("1 2 3 4 5")
    before = tuple(tokens)
    result = parse(tokens)
    after = tuple(tokens)

    assert before == after == ("1", "2", "3", "4", "5")
    assert result.value == [True]


@pytest.mark.parametrize("source,expected,parse", [
    ("", True, comb.Emit(True)),
    ("1 2 3", False, comb.Emit(False)),
    ("foo bar", "baz", comb.Emit("baz")),
    ("...", [], comb.Emit([])),
])
def test_emit_parse_valid(source: str,
                          expected: t.Any,
                          parse: comb.Parser,
                          ) -> None:
    """Emit(val) parser should emit val without modifying tokens."""
    tokens = as_tokens(source)
    before = len(tokens)
    assert parse(tokens).value == expected
    after = len(tokens)
    assert before == after


def test_eof_parse() -> None:
    """Parser result should be empty if there are no tokens, or raise error."""
    parse = comb.Eof()
    for source in ("", [], ()):
        result = parse(as_tokens(source))
        assert result.empty
        assert result.value is None

    for source in ("foo", ["bar", "baz"]):
        with pytest.raises(comb.CantParse):
            parse(as_tokens(source))


@pytest.mark.parametrize("source,expected", [
    ("1", True),
    ("t", True),
    ("T", True),
    ("trUe", True),
    ("true", True),
    ("True", True),
    ("TRUE", True),
    ("y", True),
    ("Y", True),
    ("yEs", True),
    ("YES", True),
    ("yes yes", True),
    (" 0", False),
    ("f", False),
    ("F", False),
    ("falSe", False),
    ("false", False),
    ("False", False),
    ("FALSE", False),
    ("n", False),
    ("N ", False),
    ("No", False),
    ("NO", False),
    ("no no no", False),
])
def test_bool_parse_valid(source: str, expected: bool) -> None:
    """Bool() parser should only parse tokens above (case-insensitive)."""
    parse = comb.Bool()
    assert parse(as_tokens(source)).value == expected


@pytest.mark.parametrize("source", ["yy", "oh no", "2", ""])
def test_bool_parse_invalid(source: str) -> None:
    """Bool() parser should raise CantParse."""
    parse = comb.Bool()
    with pytest.raises(comb.CantParse):
        parse(as_tokens(source))


@pytest.mark.parametrize("expected,parser", [
    ("int", comb.One(int)),
    ("''", comb.Or(comb.Emit(False), comb.Emit(True))),
    ("str", comb.Or(comb.One(str))),
    ("[float]", comb.Or(comb.One(float), comb.Emit(True))),
    ("(int | float | str)", comb.Or(
        comb.One(int), comb.One(float), comb.One(str)
    )),
    ("''", comb.And(comb.Emit(False))),
    ("int", comb.And(comb.One(int))),
    ("((int | float) (int | float))", comb.And(
        comb.Or(comb.One(int), comb.One(float)),
        comb.Or(comb.One(int), comb.One(float)),
    )),
    ("''", comb.Repeat(comb.Or(comb.And()))),
    ("[(str str)...]", comb.Repeat(comb.And(comb.One(str), comb.One(str)))),
    ("''", comb.Emit(None)),
    ("''", comb.Eof()),
    ("bool", comb.Bool()),
])
def test_parser_str(parser: comb.Parser, expected: str) -> None:
    """Test Parser.__str__."""
    assert str(parser) == expected


def test_parser_pretty() -> None:
    """Parser.pretty should use template."""
    assert comb.Repeat(comb.One(int)).pretty() == "<[int...]>"

    parser = comb.And(comb.Or(comb.One(float), comb.Emit(False)))
    assert parser.pretty("test: {}, bye.") == "test: [float], bye."


@given(st.one_of(st.integers(), st.text(), st.floats(allow_nan=False)))
def test_lit_str(value: t.Any) -> None:
    """str(Parser) should be the same as str(value)."""
    parser = comb.Lit(value)
    assert str(parser) == str(value)
    result = parser(collections.deque([str(value)]))
    assert result.value == value
