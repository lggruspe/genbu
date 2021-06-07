"""Forward options and arguments to function."""

import inspect
import typing as t

from ..exceptions import CLError


class MissingArgument(CLError):
    """Missing argument to function."""


def to_args_kwargs(optargs: dict[str, t.Any],
                   function: t.Callable[..., t.Any],
                   ) -> tuple[list[t.Any], dict[str, t.Any]]:
    """Convert optargs to (args, kwargs).

    Does not check returned args and kwargs.
    """
    args = []
    kwargs = {}

    sig = inspect.signature(function)
    for name, param in sig.parameters.items():
        value = optargs.get(name, param.default)
        if value is param.empty:
            raise MissingArgument(
                f"{function.__name__}() missing required argument: '{name}'"
            )
        if param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD):
            args.append(value)
        elif param.kind == param.VAR_POSITIONAL:
            args.extend(value)
        elif param.kind == param.KEYWORD_ONLY:
            kwargs[name] = value
        else:
            assert param.kind == param.VAR_KEYWORD
            kwargs.update(value)
    return args, kwargs
