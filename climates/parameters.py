"""Set subparser parameters."""

from argparse import ArgumentParser
from functools import wraps
from inspect import Parameter
from typing import Any, Callable, Optional


def caster(annotation: Callable[..., Any]) -> Callable[..., Any]:
    """Wrap around callable annotation so that invalid conversions just return
    the input.
    """
    @wraps(annotation)
    def wrapper(arg: Any) -> Any:
        """Just return the input if conversion fails."""
        try:
            return annotation(arg)
        except (TypeError, ValueError):
            return arg
    return wrapper


def get_type(param: Parameter) -> Optional[Any]:
    """Get type annotation if there's any and if it's callable."""
    if param.annotation is param.empty or not callable(param.annotation):
        return None
    return caster(param.annotation)


def set_positional_only(subparser: ArgumentParser, param: Parameter) -> None:
    """Add positional only argument to subparser."""
    if param.default is not param.empty:
        subparser.add_argument(param.name, type=get_type(param),
                               nargs='?', default=param.default)
    else:
        subparser.add_argument(param.name, type=get_type(param))


def set_var_positional(subparser: ArgumentParser, param: Parameter) -> None:
    """Add var positional argument to subparser."""
    subparser.add_argument(f"--{param.name}", nargs='*', type=get_type(param),
                           default=())


def set_keyword_only(subparser: ArgumentParser, param: Parameter) -> None:
    """Add keyword only argument to subparser."""
    if param.default is not param.empty:
        subparser.add_argument(f"--{param.name}", type=get_type(param),
                               nargs='?', default=param.default)
    else:
        subparser.add_argument(f"--{param.name}", type=get_type(param),
                               required=True)


def set_var_keyword(subparser: ArgumentParser, param: Parameter) -> None:
    """Add var keyword argument to subparser."""
    # syntax: --name 'key1:val1' 'key2:val2' ...
    subparser.add_argument(f"--{param.name}", type=str, nargs='*', default=())


HANDLERS = {
    Parameter.POSITIONAL_ONLY: set_positional_only,
    Parameter.POSITIONAL_OR_KEYWORD: set_keyword_only,
    Parameter.VAR_POSITIONAL: set_var_positional,
    Parameter.KEYWORD_ONLY: set_keyword_only,
    Parameter.VAR_KEYWORD: set_var_keyword,
}


def add(subparser: ArgumentParser, param: Parameter) -> None:
    """Add argument to subparser."""
    HANDLERS[param.kind](subparser, param)
