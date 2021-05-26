"""Shell parser."""

import collections
import textwrap
import typing as t

from .exceptions import CliException
from .namespace import Namespace
from .params import Param, Renamer, UnknownOption, check_arguments, partition


ExceptionHandler = t.Callable[[CliException], t.NoReturn]


def _exception_handler(exc: CliException) -> t.NoReturn:
    """Default exception handler."""
    raise exc


class ShellParser:  # pylint: disable=R0902,R0913
    """Shell (argv) parser."""
    def __init__(self,
                 name: str,
                 description: str,
                 params: t.Optional[list[Param]] = None,
                 subparsers: t.Optional[t.Sequence["ShellParser"]] = None,
                 exception_handler: ExceptionHandler = _exception_handler,
                 function: t.Optional[t.Callable[..., t.Any]] = None,
                 ):
        assert not any(c.isspace() for c in name)

        self.name = name
        self.description = textwrap.dedent(description.strip())
        self.params = list(params or ())
        self.subparsers = {s.name: s for s in subparsers or []}
        self.exception_handler = exception_handler
        self.function = function

        self.rename = Renamer(params or ())
        self.options = {}
        self.arguments = {}

        for param in params or ():
            for optarg in param.optargs:
                if optarg.startswith("-"):
                    self.options[optarg] = param
                else:
                    self.arguments[optarg] = param

    def expand(self, prefix: str) -> str:
        """Expand prefix to long option.

        Return prefix if it's a short option and it exists.
        Otherwise, raise UnknownOption.
        Also raise error if the prefix is ambiguous.
        """
        if not prefix.startswith("--"):
            if prefix in self.options:
                return prefix
            raise UnknownOption(prefix)

        candidates = [o for o in self.options if o.startswith(prefix)]
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
        param = self.options.get(name)
        if param is None:
            raise UnknownOption(name)
        parse = param.parse

        deque = collections.deque(args)
        value = parse(deque).value
        return (name, value, list(deque))

    def takes_params(self) -> bool:
        """Check if ShellParser can directly take Params."""
        return bool(self.params)

    def has_subcommands(self) -> bool:
        """Check if ShellParser has named subcommands."""
        return bool(self.subparsers)

    def __call__(self, argv: t.Sequence[str]) -> Namespace:
        """Parse commands, options and arguments from argv.

        Parse argv in three passes.
        0. Parse commands.
        1. Parse options.
        2. Parse arguments.

        Note: parsers may throw CantParse.
        Long option expansion may raise UnknownOption.
        """
        try:
            return self._call(argv)
        except CliException as exc:
            self.exception_handler(exc)

    def _call(self, argv: t.Sequence[str]) -> Namespace:
        """__call__ implementation."""
        route: list["ShellParser"] = []
        deque = collections.deque(argv)

        while deque:
            prev = len(route)
            for name, sub in self.subparsers.items():
                if name == deque[0]:
                    route.append(sub)
                    deque.popleft()
                    break
            if prev == len(route):
                break

        subparser = route[-1] if route else self
        optargs = self.parse_optargs(subparser, deque)
        return Namespace(optargs, tuple(s.name for s in route) or None)

    @staticmethod
    def parse_optargs(subparser: "ShellParser",
                      argv: t.Sequence[str],
                      ) -> dict[str, t.Any]:
        """Parse options and arguments from argv using custom subparser.

        Assume program name and subcommands have been removed.
        """
        args, opts = partition(argv)
        optargs = []

        for opt in opts:
            if opt[0].startswith("-") and not opt[0].startswith("--"):
                for short in opt[0][1:]:
                    name, value, unused = subparser.parse_opt(f"-{short}",
                                                              opt[1:])
                    optargs.append((name, value))
                    args.extend(unused)
                continue
            name, value, unused = subparser.parse_opt(opt[0], opt[1:])
            optargs.append((name, value))
            args.extend(unused)

        deque = collections.deque(args)
        for name, param in subparser.arguments.items():
            optargs.append((name, param.parse(deque).value))

        if deque:
            raise UnknownOption(deque[0])

        renamed = subparser.rename(optargs)
        if not subparser.function:
            return renamed
        return check_arguments(renamed, subparser.function)
