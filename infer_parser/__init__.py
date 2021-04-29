"""Shell arguments parser."""

from collections import abc
import dataclasses
import functools
import math
import types
import typing as t


class CantParse(ValueError):
    """Cannot parse tokens (list[str])."""


class UnsupportedType(TypeError):
    """Unsupported type."""


@dataclasses.dataclass
class Parser:
    """Arguments parser."""
    hint: t.Any
    function: t.Callable[[list[str]], t.Any]
    length: t.Union[int, float] = 1

    def __call__(self, tokens: abc.Sequence[str]) -> t.Any:
        """Run parsing function on list of tokens."""
        return self.function(tokens)  # type: ignore


def destructure(hint: t.Any) -> tuple[t.Any, tuple[t.Any, ...]]:
    """Return type hint origin and args."""
    return t.get_origin(hint), t.get_args(hint)


def make_simple_parser(hint: t.Any,
                       function: t.Callable[..., t.Any]
                       ) -> Parser:
    """Make parser out of callable."""
    @functools.wraps(function)
    def wrapper(tokens: abc.Sequence[str]) -> t.Any:
        if len(tokens) != 1:
            raise CantParse(hint, tokens)
        try:
            return function(tokens[0])
        except Exception as exc:
            raise CantParse(hint, tokens) from exc
    return Parser(hint, wrapper)


def make_annotated_parser(hint: t.Any) -> Parser:
    """Return parser for Final and Annotated types."""
    origin, args = destructure(hint)
    assert origin in (t.Annotated, t.Final)
    assert len(args) > 0
    return make_parser(args[0])


def make_union_parser(hint: t.Any) -> Parser:
    """Return union of parsers of hint args.

    Note: result length is an integer if every arg has the same parser.length.
    Otherwise, it is math.inf.
    """
    origin, args = destructure(hint)
    assert origin is t.Union
    parsers = [make_parser(arg) for arg in args]

    def function(tokens: abc.Sequence[str]) -> t.Any:
        for parse in parsers:
            try:
                return parse(tokens)
            except Exception:  # pylint: disable=broad-except
                pass
        raise CantParse(hint, tokens)

    lengths = set(p.length for p in parsers)
    length = lengths.pop() if len(lengths) == 1 else math.inf
    return Parser(hint, function, length)


def make_list_parser(hint: t.Any) -> Parser:
    """Return list parser."""
    origin, args = destructure(hint)
    assert origin in (list, t.List)
    if len(args) != 1:
        raise UnsupportedType(hint)
    parse = make_parser(args[0])
    if parse.length == math.inf:
        raise UnsupportedType(hint)

    def function(tokens: abc.Sequence[str]) -> list[t.Any]:
        assert isinstance(parse.length, int)

        if len(tokens) % parse.length != 0:
            raise CantParse(hint, tokens)
        return [
            parse(tokens[i:i + parse.length])
            for i in range(0, len(tokens), parse.length)
        ]
    return Parser(hint, function, math.inf)


def make_dict_parser(hint: t.Any) -> Parser:
    """Return dict parser."""
    origin, args = destructure(hint)
    assert origin in (dict, t.Dict)
    if len(args) != 2:
        raise UnsupportedType(hint)

    parse_key = make_parser(args[0])
    parse_val = make_parser(args[1])
    if parse_key.length == math.inf:
        raise UnsupportedType(hint)
    if parse_val.length == math.inf:
        raise UnsupportedType(hint)

    assert isinstance(parse_key.length, int)
    assert isinstance(parse_val.length, int)
    length: int = parse_key.length + parse_val.length

    def function(tokens: abc.Sequence[str]) -> dict[t.Any, t.Any]:
        assert isinstance(parse_key.length, int)
        assert isinstance(parse_val.length, int)

        if len(tokens) % length != 0:
            raise CantParse(hint, tokens)
        keys = []
        vals = []
        for i in range(0, len(tokens), length):
            keys.append(parse_key(tokens[i:i + parse_key.length]))
            vals.append(parse_val(tokens[i + parse_key.length:i + length]))
        return dict(zip(keys, vals))

    return Parser(hint, function, math.inf)


def make_variable_length_tuple_parser(hint: t.Any) -> Parser:
    """Return parser for variable-length tuple."""
    origin, args = destructure(hint)
    assert origin in (tuple, t.Tuple)
    assert ... in args
    if len(args) != 2 or args[0] == ...:
        raise UnsupportedType(hint)

    parse = make_parser(args[0])
    if parse.length == math.inf:
        raise UnsupportedType(hint)
    assert isinstance(parse.length, int)

    def function(tokens: abc.Sequence[str]) -> tuple[t.Any, ...]:
        assert isinstance(parse.length, int)
        if len(tokens) % parse.length != 0:
            raise CantParse(hint, tokens)
        return tuple(parse(tokens[i:i + parse.length])
                     for i in range(0, len(tokens), parse.length))
    return Parser(hint, function, math.inf)


def make_fixed_length_tuple_parser(hint: t.Any) -> Parser:
    """Return parser for fixed-length tuple.

    Note: fixed-length refers to root tuple.
    It may still contain variable-length tuples.
    """
    origin, args = destructure(hint)
    assert origin in (tuple, t.Tuple)
    assert ... not in args
    parsers = [make_parser(arg) for arg in args]
    lengths = [p.length for p in parsers]
    if any(length == math.inf for length in lengths[:-1]):
        raise UnsupportedType(hint)

    def function(tokens: abc.Sequence[str]) -> tuple[t.Any, ...]:
        value = []
        start = 0
        for parse in parsers[:-1]:
            assert isinstance(parse.length, int)
            value.append(parse(tokens[start:start + parse.length]))
            start += parse.length
        value.append(parsers[-1](tokens[start:]))
        return tuple(value)
    return Parser(hint, function, sum(lengths))


def make_tuple_parser(hint: t.Any) -> Parser:
    """Make tuple parser."""
    origin, args = destructure(hint)
    assert origin in (tuple, t.Tuple)
    if ... in args:
        return make_variable_length_tuple_parser(hint)
    return make_fixed_length_tuple_parser(hint)


def parse_bool(string: str) -> bool:
    """Parse '1', 't', 'true', '0' 'f', 'no', 'false', etc. to bool."""
    lower = string.lower()
    if lower in ("1", "t", "true", "y", "yes"):
        return True
    if lower in ("0", "f", "false", "n", "no"):
        return False
    raise CantParse(bool, [string])


def parse_none(string: str) -> None:
    """Parse '', 'none', 'None' as None."""
    if string in ("", "none", "None"):
        return None
    raise CantParse(None, [string])


PARSERS = {
    None: make_simple_parser(None, parse_none),
    bool: make_simple_parser(bool, parse_bool),
    type(None): make_simple_parser(None, parse_none),
}

PARSER_MAKERS = {
    dict: make_dict_parser,
    list: make_list_parser,
    t.Annotated: make_annotated_parser,
    t.Dict: make_dict_parser,
    t.Final: make_annotated_parser,
    t.List: make_list_parser,
    t.Tuple: make_tuple_parser,
    t.Union: make_union_parser,
    tuple: make_tuple_parser,
}


def cache(parser: Parser) -> Parser:
    """Cache and return parser."""
    origin, _ = destructure(parser.hint)
    assert origin is None
    PARSERS[parser.hint] = parser
    return parser


def make_parser(hint: t.Any) -> Parser:
    """Make parser for type hint.

    Caches simple types so that rerunning make_parser will give the same
    result. Don't cache types with parameters, because it doesn't work with
    Union and possibly other types.
    """
    if (parser := PARSERS.get(hint)) is not None:
        return parser
    if isinstance(hint, type) and not isinstance(hint, types.GenericAlias):
        return cache(make_simple_parser(hint, hint))
    origin, _ = destructure(hint)
    if (maker := PARSER_MAKERS.get(origin)) is not None:
        return maker(hint)
    raise UnsupportedType(hint)
