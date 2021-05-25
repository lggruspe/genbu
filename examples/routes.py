import sys
from tortoise import (
    CliException,
    Param,
    ParamsParser,
    Router,
    Subcommand,
    forward,
    combinators as comb,
    usage,
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


def throw():
    raise CliException


try:
    command, optargs = router(sys.argv[1:])
    function = (
        cat.cat if command.name == ("cat",) else
        hello.hello if command.name == ("hello",) else
        throw
    )
    print(forward(optargs, function))
except CliException:
    footer = "Try 'router <command> -h' for more information."
    usage("router", "Tortoise CLI example with subcommands.", footer, router)
except Exception as exc:
    print("something went wrong:", exc)
