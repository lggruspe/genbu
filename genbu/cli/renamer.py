"""Rename parameters in options and arguments and resolve name conflicts."""

import typing as t

from ..params import Param


Resolver = t.Callable[[t.Any, t.Any], t.Any]


def rename(optargs: t.List[t.Tuple[str, t.Any]],
           name: str,
           names: t.Set[str],
           resolve: Resolver,
           ) -> t.List[t.Tuple[str, t.Any]]:
    """Rename parameters in optargs and resolve name conflicts."""
    renamed = []
    none = object()
    final: t.Any = none
    for param, value in optargs:
        if param in names:
            final = value if final is none else resolve(final, value)
        else:
            renamed.append((param, value))
    if final is not none:
        renamed.append((name, final))
    return renamed


class Renamer:  # pylint: disable=too-few-public-methods
    """Options and arguments renamer."""
    def __init__(self, params: t.Sequence[Param]):
        self.params = params

    def __call__(self,
                 optargs: t.List[t.Tuple[str, t.Any]],
                 ) -> t.Dict[str, t.Any]:
        """Rename parameters and convert into dict."""
        for param in self.params:
            optargs = rename(
                optargs,
                param.name,
                set(param.optargs),
                param.resolve
            )
        return dict(optargs)
