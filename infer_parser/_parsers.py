"""Make shell arguments parsers from type hints."""

import sys
import typing as t

from genbu import combinators as comb


class UnsupportedType(TypeError):
    """Unsupported type."""


def make_optional_parser(arg: t.Any) -> comb.Parser:
    """Return parser for t.Optional[arg]."""
    return comb.Or(make_parser(arg), make_parser(type(None)))


def make_union_parser(*args: t.Any) -> comb.Parser:
    """Return parser for t.Union[args]."""
    if len(args) == 2 and type(None) in args:
        arg = args[0] if args[0] is not type(None) else args[1]  # noqa:E721
        return make_optional_parser(arg)
    return comb.Or(*map(make_parser, args))


def make_list_parser(arg: t.Any) -> comb.Parser:
    """Return parser for list[arg] and t.List[arg]."""
    return comb.Repeat(make_parser(arg))


def make_dict_parser(key: t.Any, val: t.Any) -> comb.Parser:
    """Return parser for dict[key, val] and t.Dict[key, val]."""
    return comb.Repeat(comb.And(make_parser(key), make_parser(val)), then=dict)


def make_tuple_parser(*args: t.Any) -> comb.Parser:
    """Return parser for tuple[args] and t.Tuple[args]."""
    if not args:
        raise UnsupportedType(t.Tuple[args])

    if len(args) == 2 and args[-1] == ...:
        return comb.Repeat(make_parser(args[0]), then=tuple)
    return comb.And(*map(make_parser, args), then=tuple)


def destructure(hint: t.Any) -> t.Tuple[t.Any, t.Tuple[t.Any, ...]]:
    """Return type hint origin and args."""
    return t.get_origin(hint), t.get_args(hint)


def is_generic_alias(hint: t.Any) -> bool:
    """Check if hint is a generic alias."""
    return t.get_origin(hint) is not None


class ParserMaker:
    """Parser maker with cache."""
    def __init__(self) -> None:
        self.parsers = {
            None: comb.Emit(None),
            bool: comb.Bool(),
            type(None): comb.Emit(None),
        }
        self.parser_makers = {
            dict: make_dict_parser,
            list: make_list_parser,
            t.Dict: make_dict_parser,
            t.Final: self.make_parser,
            t.List: make_list_parser,
            t.Tuple: make_tuple_parser,
            t.Union: make_union_parser,
            tuple: make_tuple_parser,
        }

    def cache(self, hint: t.Any, parser: comb.Parser) -> comb.Parser:
        """Cache and return parser."""
        origin, _ = destructure(hint)
        assert origin is None
        self.parsers[hint] = parser
        return parser

    def make_parser(self, hint: t.Any) -> comb.Parser:
        """Make parser for type hint.

        Caches simple types so that rerunning make_parser will give the same
        result. Don't cache types with parameters, because it doesn't work with
        Union and possibly other types.
        """
        if (parser := self.parsers.get(hint)) is not None:
            return parser
        if isinstance(hint, type) and not is_generic_alias(hint):
            return self.cache(hint, comb.One(hint))

        origin, args = destructure(hint)
        if sys.version_info >= (3, 9) and origin == t.Annotated:
            return self.make_parser(args[0])
        if (maker := self.parser_makers.get(origin)) is not None:
            return maker(*args)  # type: ignore
        raise UnsupportedType(hint)


make_parser = ParserMaker().make_parser
