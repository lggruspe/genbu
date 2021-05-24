import sys
from tortoise import (
    Param, ParamsParser, Router, Subcommand, forward, combinators as comb
)

from examples import cat, hello

cli = ParamsParser([
    Param("help", ["-h", "--help"], comb.Emit(True), lambda _, b: b)
])

router = Router([
    Subcommand(cli, "", "router example"),
    Subcommand(hello.cli, "hello", "say hello"),
    Subcommand(cat.cli, "cat", "concatenate files to stdout"),
])


try:
    command, optargs = router(sys.argv[1:])
    function = (
        cat.cat if command.name == ("cat",) else
        hello.hello if command.name == ("hello",) else
        lambda: """usage: routes.py (-h | --help | <command> ...)
commands: cat, hello"""
    )
    print(forward(optargs, function))
except Exception as exc:
    sys.exit(f"something went wrong: {exc}")
