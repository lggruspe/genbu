"""Make shell arguments parsers from type hints."""

import sys
import typing as t

from genbu import combinators as comb


def make_optional_parser(arg: t.Any) -> comb.Parser:
    """Return parser for t.Optional[arg]."""
    return comb.Or(make_parser(arg), make_parser(type(None)))


def make_union_parser(*args: t.Any) -> comb.Parser:
    """Return parser for t.Union[args]."""
    if len(args) == 2 and type(None) in args:
        arg = args[0] if args[0] is not type(None) else args[1]  # noqa:E721
        return make_optional_parser(arg)
    return comb.Or(*map(make_parser, args))


class Lit(comb.Parser):
    """Literal parser.

    Type of value should implement __str__.
    """
    def __init__(self, value: t.Any):
        self.value = value

    def __str__(self) -> str:
        return str(self.value)

    def parse(self, tokens: t.Deque[str]) -> comb.Result:
        """Parse value."""
        if not tokens or tokens[0] != str(self.value):
            raise comb.CantParse(self, tokens)
        tokens.popleft()
        return comb.Result(self.value)


def make_literal_parser(*args: t.Any) -> comb.Parser:
    """Return parser for t.Literal[args]."""
    return comb.Or(*map(Lit, args))


def make_list_parser(arg: t.Any) -> comb.Parser:
    """Return parser for list[arg] and t.List[arg]."""
    return comb.Repeat(make_parser(arg))


def make_dict_parser(key: t.Any, val: t.Any) -> comb.Parser:
    """Return parser for dict[key, val] and t.Dict[key, val]."""
    return comb.Repeat(comb.And(make_parser(key), make_parser(val)), then=dict)


def make_tuple_parser(*args: t.Any) -> comb.Parser:
    """Return parser for tuple[args] and t.Tuple[args]."""
    if args in ((), ((),)):
        return comb.Emit(())
    if len(args) == 2 and args[-1] == ...:
        return comb.Repeat(make_parser(args[0]), then=tuple)
    return comb.And(*map(make_parser, args), then=tuple)


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
            t.ClassVar: self.make_parser,
            t.Dict: make_dict_parser,
            t.List: make_list_parser,
            t.Tuple: make_tuple_parser,
            t.Type: self.make_parser,
            t.Union: make_union_parser,
            tuple: make_tuple_parser,
            type: self.make_parser,
        }
        if sys.version_info >= (3, 8):
            self.parser_makers.update({
                t.Final: self.make_parser,  # pylint: disable=no-member
            })

    def cache(self, hint: t.Any, parser: comb.Parser) -> comb.Parser:
        """Cache and return parser."""
        assert get_origin(hint) is None
        self.parsers[hint] = parser
        return parser

    def make_parser(self, hint: t.Any) -> comb.Parser:
        """Make parser for type hint.

        Caches simple types so that rerunning make_parser will give the same
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
            return self.make_parser(args[0])
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


make_parser = ParserMaker().make_parser