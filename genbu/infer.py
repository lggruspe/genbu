"""Infer parser from type hint."""

import sys
import typing as t

from . import combinators as comb


def make_optional_parser(arg: t.Any) -> comb.Parser:
    """Return parser for t.Optional[arg]."""
    return comb.Or(infer_parser(arg), infer_parser(type(None)))


def make_union_parser(*args: t.Any) -> comb.Parser:
    """Return parser for t.Union[args]."""
    if len(args) == 2 and type(None) in args:
        arg = args[0] if args[0] is not type(None) else args[1]  # noqa:E721
        return make_optional_parser(arg)
    return comb.Or(*map(infer_parser, args))


def make_literal_parser(*args: t.Any) -> comb.Parser:
    """Return parser for t.Literal[args]."""
    return comb.Or(*map(comb.Lit, args))


def make_list_parser(arg: t.Any) -> comb.Parser:
    """Return parser for list[arg] and t.List[arg]."""
    return comb.Repeat(infer_parser(arg))


def make_dict_parser(key: t.Any, val: t.Any) -> comb.Parser:
    """Return parser for dict[key, val] and t.Dict[key, val]."""
    return comb.Repeat(comb.And(infer_parser(key), infer_parser(val)),
                       then=dict)


def make_tuple_parser(*args: t.Any) -> comb.Parser:
    """Return parser for tuple[args] and t.Tuple[args]."""
    if args in ((), ((),)):
        return comb.Emit(())
    if len(args) == 2 and args[-1] == ...:
        return comb.Repeat(infer_parser(args[0]), then=tuple)
    return comb.And(*map(infer_parser, args), then=tuple)


def get_origin(hint: t.Any) -> t.Any:
    """Return type hint origin."""
    try:
        return getattr(t, "get_origin")(hint)
    except AttributeError:
        return getattr(hint, "__origin__", None)


def get_args(hint: t.Any) -> t.Any:
    """Return type hint args."""
    try:
        return getattr(t, "get_args")(hint)
    except AttributeError:
        return getattr(hint, "__args__", ())


def destructure(hint: t.Any) -> t.Tuple[t.Any, t.Tuple[t.Any, ...]]:
    """Return type hint origin and args."""
    return get_origin(hint), get_args(hint)


def is_generic_alias(hint: t.Any) -> bool:
    """Check if hint is a generic alias."""
    return get_origin(hint) is not None


class UnsupportedType(TypeError):
    """Unsupported type."""


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
            t.ClassVar: self.infer_parser,
            t.Dict: make_dict_parser,
            t.List: make_list_parser,
            t.Tuple: make_tuple_parser,
            t.Type: self.infer_parser,
            t.Union: make_union_parser,
            tuple: make_tuple_parser,
            type: self.infer_parser,
        }
        if sys.version_info >= (3, 8):
            self.parser_makers.update({
                t.Final: self.infer_parser,  # pylint: disable=no-member
            })

    def cache(self, hint: t.Any, parser: comb.Parser) -> comb.Parser:
        """Cache and return parser."""
        assert get_origin(hint) is None
        self.parsers[hint] = parser
        return parser

    def infer_parser(self, hint: t.Any) -> comb.Parser:
        """Make parser for type hint.

        Caches simple types so that rerunning infer_parser will give the same
        result. Don't cache types with parameters, because it doesn't work with
        Union and possibly other types.
        """
        parser = self.parsers.get(hint)
        if parser is not None:
            return parser
        if isinstance(hint, type) and not is_generic_alias(hint):
            return self.cache(hint, comb.One(hint))

        origin, args = destructure(hint)
        if (
            sys.version_info >= (3, 9)
            and origin is t.Annotated  # pylint: disable=no-member
        ):
            return self.infer_parser(args[0])
        if (
            sys.version_info >= (3, 8)
            and origin is t.Literal  # pylint: disable=no-member
            and len(args) > 0
        ):
            return make_literal_parser(*args)

        maker = self.parser_makers.get(origin)
        if maker is not None:
            return maker(*args)  # type: ignore
        raise UnsupportedType(hint)


infer_parser = ParserMaker().infer_parser
