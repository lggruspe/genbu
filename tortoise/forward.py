"""Forward options and arguments to function."""

import inspect
import typing as t

from .commons import CliException


class MissingArgument(CliException):
    """Missing argument to function."""


def forward(optargs: dict[str, t.Any],
            function: t.Callable[..., t.Any],
            ) -> t.Any:
    """Forward options and arguments to function."""
    args = []
    kwargs = {}

    sig = inspect.signature(function)
    for name, param in sig.parameters.items():
        value = optargs.get(name, param.default)
        if value is param.empty:
            raise MissingArgument(name)
        if param.kind in (param.POSITIONAL_ONLY, param.POSITIONAL_OR_KEYWORD):
            args.append(value)
        elif param.kind == param.VAR_POSITIONAL:
            args.extend(value)
        elif param.kind == param.KEYWORD_ONLY:
            kwargs[name] = value
        else:
            assert param.kind == param.VAR_KEYWORD
            kwargs.update(value)

    return function(*args, **kwargs)
