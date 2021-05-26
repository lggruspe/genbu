"""Namespace object."""

import typing as t
from .forward import to_args_kwargs


Func = t.Callable[..., t.Any]


class Namespace:  # pylint: disable=too-few-public-methods
    """Namespace object that contains:

    - mapping from names to values
    - (optional) command prefix from argv
    """
    def __init__(self,
                 names: dict[str, t.Any],
                 command: t.Optional[tuple[str, ...]] = None):
        self.names = names
        self.command = command

    def bind(self,
             default: Func,
             lookup: t.Optional[dict[tuple[str, ...], Func]] = None,
             ) -> t.Any:
        """Pass names to function."""
        lookup = lookup or {}
        function = default
        if self.command is not None:
            function = lookup.get(self.command, default)
        args, kwargs = to_args_kwargs(self.names, function)
        return function(*args, **kwargs)
