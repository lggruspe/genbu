import sys
from tortoise import (
    CliException, Param, ShellParser, forward, combinators as comb, usage,
)
from examples import cat, hello

cli = ShellParser(
    name=__name__,
    description="router example",
    params=[
        Param("help", ["-h", "--help"], comb.Emit(True), lambda _, b: b)
    ],
    subparsers=[cat.cli, hello.cli],
)


def throw():
    raise CliException


try:
    command, optargs = cli(sys.argv[1:])
    function = (
        cat.cat if command == ("cat",) else
        hello.hello if command == ("hello",) else
        throw
    )
    print(forward(optargs, function))
except CliException:
    footer = "Try 'cli <command> -h' for more information."
    usage("cli", "Tortoise CLI example with subcommands.", footer, cli)
except Exception as exc:
    print("something went wrong:", exc)
