"""Make shell arguments parsers from type hints."""

import types
import typing as t

from genbu import combinators as comb


class UnsupportedType(TypeError):
    """Unsupported type."""


def destructure(hint: t.Any) -> t.Tuple[t.Any, t.Tuple[t.Any, ...]]:
    """Return type hint origin and args."""
    return t.get_origin(hint), t.get_args(hint)


def make_annotated_parser(hint: t.Any) -> comb.Parser:
    """Return parser for Final and Annotated types."""
    origin, args = destructure(hint)
    assert origin in (t.Annotated, t.Final)
    assert len(args) > 0
    return make_parser(args[0])


def make_optional_parser(hint: t.Any) -> comb.Parser:
    """Make Optional[...] parser."""
    origin, args = destructure(hint)
    assert origin is t.Union
    assert len(args) == 2
    assert type(None) in args

    parsers = [
        make_parser(arg) for arg in args
        if arg is not type(None)  # noqa:E721
    ]
    assert len(parsers) == 1
    return comb.Or(parsers[0], make_parser(type(None)))


def make_union_parser(hint: t.Any) -> comb.Parser:
    """Return union of parsers of hint args."""
    origin, args = destructure(hint)
    assert origin is t.Union
    if len(args) == 2 and type(None) in args:
        return make_optional_parser(hint)
    return comb.Or(*map(make_parser, args))


def make_list_parser(hint: t.Any) -> comb.Parser:
    """Return list parser."""
    origin, args = destructure(hint)
    assert origin in (list, t.List)
    if len(args) != 1:
        raise UnsupportedType(hint)
    return comb.Repeat(make_parser(args[0]))


def make_dict_parser(hint: t.Any) -> comb.Parser:
    """Return dict parser."""
    origin, args = destructure(hint)
    assert origin in (dict, t.Dict)
    if len(args) != 2:
        raise UnsupportedType(hint)
    return comb.Repeat(
        comb.And(
            make_parser(args[0]),
            make_parser(args[1]),
        ),
        then=dict,
    )


def make_variable_length_tuple_parser(hint: t.Any) -> comb.Parser:
    """Return parser for variable-length tuple."""
    origin, args = destructure(hint)
    assert origin in (tuple, t.Tuple)
    assert ... in args
    if len(args) != 2 or args[0] == ...:
        raise UnsupportedType(hint)
    return comb.Repeat(make_parser(args[0]), then=tuple)


def make_fixed_length_tuple_parser(hint: t.Any) -> comb.Parser:
    """Return parser for fixed-length tuple.

    Note: fixed-length refers to root tuple.
    It may still contain variable-length tuples.
    """
    origin, args = destructure(hint)
    assert origin in (tuple, t.Tuple)
    assert ... not in args
    parsers = [make_parser(arg) for arg in args]
    if not parsers:
        raise UnsupportedType(hint)
    return comb.And(*parsers, then=tuple)


def make_tuple_parser(hint: t.Any) -> comb.Parser:
    """Make tuple parser."""
    origin, args = destructure(hint)
    assert origin in (tuple, t.Tuple)
    if ... in args:
        return make_variable_length_tuple_parser(hint)
    return make_fixed_length_tuple_parser(hint)


PARSERS = {
    None: comb.Emit(None),
    bool: comb.Bool(),
    type(None): comb.Emit(None),
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


def cache(hint: t.Any, parser: comb.Parser) -> comb.Parser:
    """Cache and return parser."""
    origin, _ = destructure(hint)
    assert origin is None
    PARSERS[hint] = parser
    return parser


def make_parser(hint: t.Any) -> comb.Parser:
    """Make parser for type hint.

    Caches simple types so that rerunning make_parser will give the same
    result. Don't cache types with parameters, because it doesn't work with
    Union and possibly other types.
    """
    if (parser := PARSERS.get(hint)) is not None:
        return parser
    if isinstance(hint, type) and not isinstance(hint, types.GenericAlias):
        return cache(hint, comb.One(hint))
    origin, _ = destructure(hint)
    if (maker := PARSER_MAKERS.get(origin)) is not None:
        return maker(hint)
    raise UnsupportedType(hint)
