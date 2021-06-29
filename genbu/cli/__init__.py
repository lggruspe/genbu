"""CLI parser."""

import collections
import inspect
import sys
import textwrap
import typing as t

from ..exceptions import CLError
from ..infer_params import infer_params_from_signature
from ..params import Param
from .normalize import UnknownOption, normalize


ExceptionHandler = t.Callable[["Genbu", CLError], t.NoReturn]


def default_error_handler(cli: "Genbu", exc: CLError) -> t.NoReturn:
    """Default exception handler."""
    name = " ".join(cli.complete_name())
    sys.exit(f"{name}: {exc}")


def unique(items: t.Iterable[t.Any]) -> t.List[t.Any]:
    """Return distinct items in items.

    If an item is already in the result, the new value replaces the existing
    value.
    """
    result: t.Dict[t.Any, None] = {}
    for item in items:
        result[item] = item
    return list(result.values())


class Genbu:  # pylint: disable=R0902,R0913
    """Shell (argv) parser."""
    def __init__(self,
                 callback: t.Callable[..., t.Any],
                 *,
                 name: t.Optional[str] = None,
                 description: t.Optional[str] = None,
                 params: t.Optional[t.List[Param]] = None,
                 subparsers: t.Optional[t.Sequence["Genbu"]] = None,
                 error_handler: ExceptionHandler = default_error_handler):

        if name is None:
            name = callback.__name__
        if description is None:
            description = callback.__doc__

        assert name is not None
        assert not any(c.isspace() for c in name)

        self.name = name
        self.description = (
            textwrap.dedent(description.strip()) if description else None
        )
        self.params = unique(
            infer_params_from_signature(callback) if params is None else params
        )
        self.subparsers = {s.name: s for s in subparsers or []}
        self.callback = callback
        self.error_handler = error_handler
        self.parent = None

        self.options = {}
        self.arguments = {}

        for param in self.params:
            for optarg in param.optargs:
                if optarg.startswith("-"):
                    self.options[optarg] = param
                else:
                    self.arguments[optarg] = param

        for sub in self.subparsers.values():
            sub.parent = self

    def complete_name(self) -> t.Tuple[str, ...]:
        """Return complete command name (includes parents)."""
        if self.parent is None:
            return (self.name,)
        return self.parent.complete_name() + (self.name,)

    def parse_opt(self,
                  name: str,
                  args: t.Sequence[str],
                  ) -> t.Tuple[Param, t.Any, t.List[str]]:
        """Parse option.

        Return expanded Param, parsed value and unparsed tokens."""
        assert name.startswith("-")
        param = self.options.get(name)

        assert param is not None

        deque = collections.deque(args)
        value = param.parser(deque).value
        return param, value, list(deque)

    def takes_params(self) -> bool:
        """Check if Genbu can directly take Params."""
        return bool(self.params)

    def has_subcommands(self) -> bool:
        """Check if Genbu has named subcommands."""
        return bool(self.subparsers)

    def parse(self, argv: t.Iterable[str]) -> "Namespace":
        """Parse commands, options and arguments from argv.

        Parse argv in three passes.
        0. Parse commands.
        1. Parse options.
        2. Parse arguments.

        Note: parsers may throw CantParse.
        Long option expansion may raise UnknownOption.
        """
        route: t.List["Genbu"] = []
        deque = collections.deque(argv)
        try:
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
            return Namespace(optargs, route[0] if route else self)
        except CLError as exc:
            subparser = route[-1] if route else self
            subparser.error_handler(subparser, exc)

    def run(self, argv: t.Optional[t.Iterable[str]] = None) -> t.Any:
        """Parse argv and run callback."""
        if argv is None:
            argv = sys.argv[1:]
        namespace = self.parse(argv)
        return namespace.bind(namespace.cli.callback)

    @staticmethod
    def parse_optargs(subparser: "Genbu",
                      argv: t.Sequence[str],
                      ) -> t.Dict[str, t.Any]:
        """Parse options and arguments from argv using custom subparser.

        Assume program name and subcommands have been removed.
        """
        normalized = normalize(subparser.params, argv)
        args = normalized.arguments
        opts = normalized.options
        optargs: t.Dict[Param, t.List[t.Any]] = {}

        for opt in opts:
            param, value, unused = subparser.parse_opt(opt[0], opt[1:])

            values = optargs.get(param, [])
            values.append(value)
            optargs[param] = values
            args.extend(unused)

        deque = collections.deque(args)
        for param in subparser.arguments.values():
            values = optargs.get(param, [])
            values.append(param.parser(deque).value)
            optargs[param] = values

        if deque:
            raise UnknownOption(deque[0])

        aggregated = {p.dest: p.aggregator(v) for p, v in optargs.items()}
        _ = to_args_kwargs(aggregated, subparser.callback)  # Check arguments
        return aggregated


class Namespace:  # pylint: disable=too-few-public-methods
    """Namespace object that contains:

    - mapping from names to values
    - (optional) command prefix from argv
    """
    def __init__(self, names: t.Dict[str, t.Any], cli: Genbu):
        self.names = names
        self.cli = cli

    def bind(self, function: t.Callable[..., t.Any]) -> t.Any:
        """Pass names to function."""
        args, kwargs = to_args_kwargs(self.names, function)
        return function(*args, **kwargs)


class MissingArgument(CLError):
    """Missing argument to function."""
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def __str__(self) -> str:
        return f"missing argument: {self.name}"


def to_args_kwargs(optargs: t.Dict[str, t.Any],
                   function: t.Callable[..., t.Any],
                   ) -> t.Tuple[t.List[t.Any], t.Dict[str, t.Any]]:
    """Convert optargs to (args, kwargs).

    Does not check returned args and kwargs.
    """
    args = []
    kwargs = {}

    sig = inspect.signature(function)
    for name, param in sig.parameters.items():
        default = (
            param.default if param.default is not param.empty
            else () if param.kind == param.VAR_POSITIONAL
            else {} if param.kind == param.VAR_KEYWORD
            else param.empty
        )

        value = optargs.get(name, default)
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
    return args, kwargs
