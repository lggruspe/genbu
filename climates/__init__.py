"""Command-line interfaces made accessible to even simpletons."""

from argparse import ArgumentParser
from inspect import getfullargspec

def microclimate(subparsers, name, func):
    """Add and return subparser.

    Obtain command-line options from function signature.
    """
    doc = func.__doc__
    subparser = subparsers.add_parser(name, help=doc, description=doc)

    spec = getfullargspec(func)
    defaults = spec.defaults or []
    offset = len(spec.args) - len(defaults)
    for i, arg in enumerate(spec.args):
        if i < offset:
            subparser.add_argument(arg)
        else:
            subparser.add_argument(arg, nargs='?', default=defaults[i - offset])
    if spec.varargs:
        subparser.add_argument(f"--{spec.varargs}", nargs='*')
    if spec.varkw:
        subparser.add_argument(f"--{spec.varkw}", nargs='*')
        # syntax: command --varkw key1:val1 key2:val2
    # TODO handle kwonlyargs and kwonlydefaults
    return subparser

class Climate:
    def __init__(self, description):
        self.description = description
        self.commands = {}

    def add_commands(self, *args, **kwargs):
        """Add commands."""
        for arg in args:
            self.commands[arg.__name__] = arg
        for key, val in kwargs.items():
            self.commands[key] = val

    def to_argparse(self):
        """Create ArgumentParser."""
        parser = ArgumentParser(description=self.description)

        subparsers = parser.add_subparsers(title="subcommands", dest="$command")
        commands = {}
        for key, val in self.commands.items():
            commands[key] = microclimate(subparsers, key, val)
        return parser

    def invoke(self, func, namespace):
        """Invoke function on args in namespace dictionary."""
        args = []
        kwargs = {}

        spec = getfullargspec(func)
        for arg in spec.args:
            args.append(namespace.get(arg)) # TODO use defaults
        if spec.varargs:
            args.extend(namespace.get(spec.varargs, []))
        if spec.varkw:
            for option in namespace.get(spec.varkw, []):
                key, val = option.split(':', 1)
                kwargs[key] = val
        # TODO handle kwonlyargs and kwonlydefaults
        return func(*args, **kwargs)

    def run(self):
        """Run argument parser and command handler."""
        parser = self.to_argparse()
        args = vars(parser.parse_args())
        command = self.commands.get(args.get("$command"))
        if not command:
            return parser.print_usage()
        return self.invoke(command, args)
