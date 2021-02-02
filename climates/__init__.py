"""Command-line interfaces made accessible to even simpletons."""

import argparse
from inspect import getfullargspec
from typing import Any, Callable, Dict, Optional, Sequence


CommandHandler = Callable[..., Any]


def microclimate(subparsers: Any, name: str, func: CommandHandler) -> Any:
    """Add and return subparser.

    Obtain command-line options from function signature.
    """
    doc = func.__doc__
    subparser = subparsers.add_parser(name, help=doc, description=doc)

    spec = getfullargspec(func)
    defaults: Sequence[Any] = spec.defaults or ()
    offset = len(spec.args) - len(defaults)
    for i, arg in enumerate(spec.args):
        if i < offset:
            subparser.add_argument(arg)
        else:
            subparser.add_argument(arg, nargs='?',
                                   default=defaults[i - offset])
    if spec.varargs:
        subparser.add_argument(f"--{spec.varargs}", nargs='*')
    if spec.varkw:
        subparser.add_argument(f"--{spec.varkw}", nargs='*')
        # syntax: command --varkw key1:val1 key2:val2
    # TODO handle kwonlyargs and kwonlydefaults
    return subparser


def invoke(func: CommandHandler, namespace: Dict[str, Any]) -> Any:
    """Invoke function on args in namespace dictionary."""
    args = []
    kwargs = {}

    spec = getfullargspec(func)
    for arg in spec.args:
        args.append(namespace.get(arg))  # TODO use defaults
    if spec.varargs:
        args.extend(namespace.get(spec.varargs, []))
    if spec.varkw:
        for option in namespace.get(spec.varkw, []):
            key, val = option.split(':', 1)
            kwargs[key] = val
    # TODO handle kwonlyargs and kwonlydefaults
    return func(*args, **kwargs)


class Climate:
    """Climate CLI."""
    def __init__(self, description: str):
        self.description = description
        self.commands: Dict[str, CommandHandler] = {}

    def add_commands(self,
                     *args: CommandHandler,
                     **kwargs: CommandHandler) -> Any:
        """Add commands."""
        for arg in args:
            self.commands[arg.__name__] = arg
        for key, val in kwargs.items():
            self.commands[key] = val

    def to_argparse(self) -> argparse.ArgumentParser:
        """Create ArgumentParser."""
        parser = argparse.ArgumentParser(description=self.description)

        subparsers = parser.add_subparsers(title="subcommands",
                                           dest="$command")
        commands = {}
        for key, val in self.commands.items():
            commands[key] = microclimate(subparsers, key, val)
        return parser

    def run(self, args: Optional[Sequence[str]] = None) -> Any:
        """Run argument parser and command handler."""
        parser = self.to_argparse()
        _args = vars(parser.parse_args(args))
        command = self.commands.get(_args.get("$command", ""))
        if not command:
            return parser.print_usage()
        return invoke(command, _args)
