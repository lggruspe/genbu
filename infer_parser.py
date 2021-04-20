"""Infer parser from type hints."""

from functools import wraps
from types import GenericAlias
from typing import Any, Callable, Iterable, List, Union
import typing


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
    def union(string: str):
        for parse in args:
            result = parse(string)
            if not isinstance(result, CantParse):
                return result
        return CantParse()
    return union


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


def map_infer(hints: Iterable[Any]) -> Union[List[Parser], CantInfer]:
    """Map infer on hints.

    Returns CantInfer if no parser can be inferred from any one of the hints.
    """
    parsers = []
    for hint in hints:
        parser = infer(hint)
        if isinstance(parser, CantInfer):
            return parser
        parsers.append(parser)
    return parsers


def infer(hint: Any) -> Union[Parser, CantInfer]:
    """Infer parser from type hint.

    Returns CantInfer on failure.
    """
    if is_none(hint):
        return parse_none
    if hint == bool:
        return parse_bool
    if isinstance(hint, type) and not isinstance(hint, GenericAlias):
        return wrap(hint)

    origin = typing.get_origin(hint)  # See help(get_args) for supported types:
    args = typing.get_args(hint)
    parsers = map_infer(args)
    if isinstance(parsers, CantInfer):
        return parsers

    return (
        CantInfer(hint) if origin is tuple else
        CantInfer(hint) if origin is typing.Tuple else
        CantInfer(hint) if origin is typing.Literal else
        parsers[0] if origin is typing.Final else
        parsers[0] if origin is typing.Annotated else
        make_union_parser(*parsers) if origin is typing.Union else
        CantInfer(hint)
    )
