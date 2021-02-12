"""Command-line interfaces made accessible to even simpletons."""

import argparse
from inspect import getfullargspec, signature
from typing import Any, Callable, Dict, Optional, Sequence, Tuple

from .parameters import add as add_parameter


CommandHandler = Callable[..., Any]


def microclimate(subparsers: Any, name: str, func: CommandHandler) -> Any:
    """Add and return subparser.

    Obtain command-line options from function signature.
    """
    doc = func.__doc__
    subparser = subparsers.add_parser(name, help=doc, description=doc)
    for param in signature(func).parameters.values():
        add_parameter(subparser, param)
    return subparser


def parse_key_value_pair(pair: str, caster: Callable[..., Any]
                         ) -> Optional[Tuple[str, Any]]:
    """Parse strings of the form 'key:val'.

    Raise ValueError on failure.
    Try to convert val using caster (callable type annotation).
    If that doesn't work, just return the original val.
    """
    key, val = pair.split(':', 1)
    try:
        return key, caster(val)
    except (TypeError, ValueError):
        return key, val


def invoke(func: CommandHandler,
           namespace: Dict[str, Any],
           subparser: Optional[argparse.ArgumentParser] = None) -> Any:
    """Invoke function on args in namespace dictionary.

    Use subparser to generate error messages in case of error in parsing
    var keyword arguments.
    """
    args = []
    kwargs = {}

    spec = getfullargspec(func)
    for arg in spec.args:
        args.append(namespace.get(arg))
    if spec.varargs:
        args.extend(namespace.get(spec.varargs, []))
    for arg in spec.kwonlyargs:
        kwargs[arg] = namespace.get(arg)
    for option in namespace.get(spec.varkw, []):
        annotation = spec.annotations.get(spec.varkw)
        try:
            key, val = parse_key_value_pair(option, annotation)
            kwargs[key] = val
        except ValueError:
            if subparser is not None:
                subparser.error(f"argument --{spec.varkw}: key and value "
                                "should be separated by ':' as in "
                                "'key:value'")
    try:
        return func(*args, **kwargs)
    except TypeError as e:
        subparser.error(e)


class Climate:
    """Climate CLI."""
    def __init__(self, prog: str, description: Optional[str] = None):
        self.prog = prog
        self.description = description
        self.commands: Dict[str, CommandHandler] = {}
        self.subparsers: Optional[Dict[str, argparse.ArgumentParser]] = None

    def add_commands(self,
                     *args: CommandHandler,
                     **kwargs: CommandHandler) -> Any:
        """Add commands."""
        for arg in args:
            self.commands[arg.__name__] = arg
        for key, val in kwargs.items():
            self.commands[key] = val

    def to_argparse(self) -> argparse.ArgumentParser:
        """Create ArgumentParser.

        Also set self.subparsers.
        """
        parser = argparse.ArgumentParser(prog=self.prog,
                                         description=self.description)

        subparsers = parser.add_subparsers(title="subcommands",
                                           dest="$command")
        commands = {}
        for key, val in self.commands.items():
            commands[key] = microclimate(subparsers, key, val)
        self.subparsers = commands
        return parser

    def run(self, args: Optional[Sequence[str]] = None) -> Any:
        """Run argument parser and command handler."""
        parser = self.to_argparse()
        _args = vars(parser.parse_args(args))
        name = _args.get("$command", "")
        command = self.commands.get(name)
        if not command:
            return parser.print_usage()
        return invoke(command, _args, self.subparsers.get(name))
