"""Params parser."""

import collections
import typing as t

from . import combinators as comb


class UnknownOption(ValueError):
    """Unrecognized option."""


def partition(argv: t.Sequence[str]) -> tuple[list[str], list[list[str]]]:
    """Partition argv arguments and options.

    Note: the options list may still contain some positional arguments.
    Assume tokens that contain multiple short options don't take args.
    """
    args = []
    opts = []

    deque = collections.deque(argv)
    while deque:
        current = deque.popleft()
        if not current.startswith("-"):
            args.append(current)
        elif not current.startswith("--") and len(current) > 2:
            for opt in current[1:]:
                opts.append([f"--{opt}"])
        else:
            tail = [current]
            while deque and not deque[0].startswith("-"):
                tail.append(deque.popleft())
            opts.append(tail)
    return args, opts


class ParamsParser:
    """Argv parser."""
    def __init__(self, parsers: dict[str, comb.Parser]):
        self.opt_parsers = {
            k: v for k, v in parsers.items() if k.startswith("-")
        }
        self.arg_parsers = [
            (k, v) for k, v in parsers.items() if not k.startswith("-")
        ]

    def expand(self, prefix: str) -> str:
        """Expand prefix to long option.

        Return prefix if it's a short option and it exists.
        Otherwise, raise UnknownOption.
        Also raise error if the prefix is ambiguous.
        """
        if not prefix.startswith("--"):
            if prefix in self.opt_parsers:
                return prefix
            raise UnknownOption(prefix)

        candidates = [o for o in self.opt_parsers if o.startswith(prefix)]
        if len(candidates) != 1:
            raise UnknownOption(prefix)
        return candidates[0]

    def parse_opt(self,
                  prefix: str,
                  args: t.Sequence[str],
                  ) -> tuple[str, t.Any, list[str]]:
        """Parse option.

        Return expanded option name, parsed value and unparsed tokens."""
        assert prefix.startswith("-")
        name = self.expand(prefix)
        parse = self.opt_parsers.get(name)
        if parse is None:
            raise UnknownOption(name)

        deque = collections.deque(args)
        value = parse(deque).value
        return (name, value, list(deque))

    def __call__(self, argv: t.Sequence[str]) -> list[tuple[str, t.Any]]:
        """Parse options and arguments from argv.

        Parse argv in two passes.
        1. Parse options.
        2. Parse arguments.

        Note: parsers may throw CantParse.
        Long option expansion may raise UnknownOption.
        """
        args, opts = partition(argv)
        optargs = []

        for opt in opts:
            if opt[0].startswith("-") and not opt[0].startswith("--"):
                for short in opt[0][1:]:
                    name, value, unused = self.parse_opt(f"-{short}", opt[1:])
                    optargs.append((name, value))
                    args.extend(unused)
                continue
            name, value, unused = self.parse_opt(opt[0], opt[1:])
            optargs.append((name, value))
            args.extend(unused)

        deque = collections.deque(args)
        for name, parse in self.arg_parsers:
            optargs.append((name, parse(deque).value))

        if deque:
            raise UnknownOption(deque[0])
        return optargs


Resolver = t.Callable[[t.Any, t.Any], t.Any]


def rename(optargs: list[tuple[str, t.Any]],
           name: str,
           names: set[str],
           resolve: Resolver,
           ) -> list[tuple[str, t.Any]]:
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


class Renamer:
    """Options and arguments renamer."""
    def __init__(self) -> None:
        self.queue: list[tuple[str, set[str], Resolver]] = []

    def add(self,
            name: str,
            *names: str,
            resolve: Resolver = lambda _, b: b,
            ) -> "Renamer":
        """Add rename task.

        All the options and arguments in names are renamed to the value of
        `name`. The resolve callback is used to resolve name conflicts.
        """
        self.queue.append((name, set(names), resolve))
        return self

    def __call__(self, optargs: list[tuple[str, t.Any]]) -> dict[str, t.Any]:
        """Rename parameters and convert into dict."""
        for name, names, resolve in self.queue:
            optargs = rename(optargs, name, names, resolve)
        return dict(optargs)
