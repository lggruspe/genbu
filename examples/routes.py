import sys
from tortoise import (
    CliException, Param, ShellParser, combinators as comb, usage,
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
    names = cli(sys.argv[1:])
    print(names.bind(throw, {
        ("cat",): cat.cat,
        ("hello",): hello.hello,
    }))
except CliException:
    footer = "Try 'cli <command> -h' for more information."
    usage("cli", "Tortoise CLI example with subcommands.", footer, cli)
except Exception as exc:
    print("something went wrong:", exc)
