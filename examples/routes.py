import sys
from tortoise import (
    CliException, Param, ShellParser, combinators as comb, usage,
)
from examples import cat, hello


def show_usage(cli: ShellParser, error: bool = False):
    name = " ".join(cli.complete_name()) or "cli"
    footer = f"Try '{name} -h' for more information."
    usage(name, "Tortoise CLI example with subcommands.", footer, cli)
    sys.exit(1 if error else 0)


def exception_handler(cli: ShellParser, exc: CliException):
    show_usage(cli, error=True)


cli = ShellParser(
    name=sys.argv[0],
    description="router example",
    params=[
        Param("help", ["-h", "--help"], comb.Emit(True), lambda _, b: b)
    ],
    subparsers=[cat.cli, hello.cli],
    exception_handler=exception_handler,
)


try:
    names = cli(sys.argv[1:])
    print(names.bind(lambda: show_usage(cli), {
        ("cat",): cat.cat,
        ("hello",): hello.hello,
    }))
except Exception as exc:
    print("something went wrong:", exc)
