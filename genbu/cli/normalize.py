"""Normalize CLI inputs."""

import typing as t

from ..exceptions import CLError
from ..params import Param


class UnknownOption(CLError):
    """Unrecognized option."""
    def __init__(self, option: str):
        super().__init__()
        self.option = option

    def __str__(self) -> str:
        return f"received unrecognized option: {self.option}"


class AmbiguousOption(UnknownOption):
    """Ambiguous long option prefix."""
    def __init__(self, prefix: str, choices: t.List[str]):
        super().__init__(prefix)
        self.prefix = prefix
        self.choices = choices

    def __str__(self) -> str:
        message = f"cannot expand ambiguous option: {self.prefix}"
        message += " could be any of "
        message += ", ".join(self.choices)
        return message


class Argv:
    """Normalized CLInterface argv."""
    def __init__(self,
                 options: t.Optional[t.List[t.List[str]]] = None,
                 arguments: t.Optional[t.List[str]] = None):
        self.options = options or []
        self.arguments = arguments or []
        self.current: t.List[str] = []

    def add_arg(self, arg: str) -> None:
        """Add argument to global arguments or to current option."""
        (self.current if self.current else self.arguments).append(arg)

    def add_opt(self, opt: str) -> None:
        """Add option."""
        self.flush()
        self.current.append(opt)

    def flush(self) -> None:
        """Save current option and trailing arguments."""
        if self.current:
            self.options.append(self.current)
            self.current = []


def complete(options: t.Dict[str, Param], prefix: str) -> str:
    """Complete long option prefix.

    Raise error if prefix is invalid or ambiguous.
    """
    assert prefix.startswith("--")
    candidates = [o for o in options if o.startswith(prefix)]
    if not candidates:
        raise UnknownOption(prefix)
    if len(candidates) > 1:
        raise AmbiguousOption(prefix, candidates)
    return candidates[0]


def is_stacked(options: t.Container[str], opts: str) -> bool:
    """Check if short options in opts are all valid."""
    assert opts.startswith("-")
    return all(f"-{opt}" in options for opt in opts[1:])


def _handle_long_option(normalized: Argv,
                        options: t.Dict[str, Param],
                        token: str,
                        ) -> None:
    """Handle long option token from argv."""
    if "=" not in token:
        normalized.add_opt(complete(options, token))
    else:
        prefix, arg = token.split("=", 1)
        normalized.add_opt(complete(options, prefix))
        normalized.add_arg(arg)
        normalized.flush()


def _handle_short_option(normalized: Argv,
                         options: t.Dict[str, Param],
                         token: str,
                         ) -> None:
    """Handle short option token from argv."""
    if "=" in token:
        option, arg = token.split("=", 1)
        if option not in options:
            raise UnknownOption(option)
        normalized.add_opt(option)
        normalized.add_arg(arg)
        normalized.flush()
    elif token in options:
        normalized.add_opt(token)
    elif is_stacked(options, token):
        for opt in token[1:]:
            normalized.add_opt(f"-{opt}")
        normalized.flush()
    elif token[:2] in options:
        normalized.add_opt(token[:2])
        arg = token[2:]
        normalized.add_arg(arg if not arg.startswith("=") else arg[1:])
        normalized.flush()
    else:
        raise UnknownOption(token)


def normalize(params: t.Iterable[Param], argv: t.Iterable[str]) -> Argv:
    """Normalize argv."""
    options = {o: p for p in params for o in p.optargs if o.startswith("-")}
    normalized = Argv()

    for token in argv:
        if token.startswith("--"):
            _handle_long_option(normalized, options, token)
        elif token.startswith("-"):
            _handle_short_option(normalized, options, token)
        else:
            normalized.add_arg(token)

    normalized.flush()
    return normalized
