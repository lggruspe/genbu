"""Infer parser from type hints."""

from functools import wraps
import shlex
import typing
from types import GenericAlias
from typing import Any, Callable, Iterable, List, Union


class CantParse(Exception):
    """Returned by wrapped parsers."""


class CantInfer(Exception):
    """Returned by infer."""


Parser = Callable[[str], Union[Any, CantParse]]


def wrap(parser: Parser) -> Parser:
    """Wrap parser to return CantParse on error."""
    @wraps(parser)
    def wrapper(*args, **kwargs):
        try:
            return parser(*args, **kwargs)
        except Exception:  # pylint: disable=broad-except
            return CantParse()
    return wrapper


def make_union_parser(*args: Parser) -> Parser:
    """Create parser that tries each parser in args one by one."""
    def union_parser(string: str):
        for parse in args:
            result = parse(string)
            if not isinstance(result, CantParse):
                return result
        return CantParse()
    return union_parser


ParseEllipsis = str  # used to identify ... from infer result


def make_variable_length_tuple_parser(parse: Parser) -> Parser:
    """Create shell string to variable-length tuple parser."""
    def variable_length_tuple_parser(string: str):
        result = tuple(map(parse, shlex.split(string)))
        if any(isinstance(r, CantParse) for r in result):
            return CantParse()
        return result
    return variable_length_tuple_parser


def make_fixed_length_tuple_parser(*args: Parser) -> Parser:
    """Create shell string to fixed-length tuple parser."""
    def tuple_parser(string: str):
        strings = shlex.split(string)
        if len(strings) != len(args):
            return CantParse()
        result = tuple(parse(s) for parse, s in zip(args, strings))
        if any(isinstance(r, CantParse) for r in result):
            return CantParse()
        return result
    return tuple_parser


def make_tuple_parser(*args: Parser) -> Union[Parser, CantInfer]:
    """Create shell string to tuple parser."""
    if ParseEllipsis in args:
        if len(args) != 2:
            return CantInfer()
        if args[0] == ParseEllipsis:
            return CantInfer()
        return make_variable_length_tuple_parser(args[0])
    return make_fixed_length_tuple_parser(*args)


def make_list_parser(*args: Parser) -> Union[Parser, CantInfer]:
    """Create shell string to list parser."""
    if len(args) != 1:
        return CantInfer()
    parse = args[0]

    def list_parser(string: str):
        result = [parse(s) for s in shlex.split(string)]
        if any(isinstance(r, CantParse) for r in result):
            return CantParse()
        return result
    return list_parser


def parse_none(string: str) -> Union[None, CantParse]:
    """Parse '' or 'None' to None."""
    if string in ("", "None"):
        return None
    return CantParse()


def parse_bool(string: str) -> Union[bool, CantParse]:
    """Parse '', 'true', 'false', 'True', 'False', '0' and '1'."""
    if string in ("true", "True", "1"):
        return True
    if string in ("false", "False", "", "0"):
        return False
    return CantParse()


def is_none(hint: Any) -> bool:
    """Check if hint is None."""
    if hint is None:
        return True
    try:
        return isinstance(None, hint)
    except TypeError:
        return False


def map_infer(hints: Iterable[Any],
              allow_ellipsis: bool = False) -> Union[List[Parser], CantInfer]:
    """Map infer on hints.

    Returns CantInfer if no parser can be inferred from any one of the hints.
    """
    parsers = []
    for hint in hints:
        parser = infer(hint)
        if isinstance(parser, CantInfer):
            return parser
        if not allow_ellipsis and parser == ParseEllipsis:
            return CantInfer()
        parsers.append(parser)
    return parsers


def infer(hint: Any) -> Union[Parser, CantInfer]:
    """Infer parser from type hint.

    Returns CantInfer on failure.
    """
    if hint == ...:
        return ParseEllipsis
    if is_none(hint):
        return parse_none
    if hint == bool:
        return parse_bool
    if isinstance(hint, type) and not isinstance(hint, GenericAlias):
        return wrap(hint)

    origin = typing.get_origin(hint)  # See help(get_args) for supported types:
    args = typing.get_args(hint)

    allow_ellipsis = origin in (tuple, typing.Tuple)
    parsers = map_infer(args, allow_ellipsis=allow_ellipsis)
    if isinstance(parsers, CantInfer):
        return parsers

    return (
        make_tuple_parser(*parsers) if origin in (tuple, typing.Tuple) else
        make_list_parser(*parsers) if origin in (list, typing.List) else
        CantInfer(hint) if origin is typing.Literal else
        parsers[0] if origin in (typing.Final, typing.Annotated) else
        make_union_parser(*parsers) if origin is typing.Union else
        CantInfer(hint)
    )
