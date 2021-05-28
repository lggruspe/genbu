from pathlib import Path
import sys
from tortoise import (
    CliException, Param, ShellParser, combinators as comb, usage
)


def cat(path: Path) -> str:
    """Concatenate contents of path to stdout."""
    return path.read_text()


def exception_handler(cli: ShellParser, exc: CliException):
    name = " ".join(cli.complete_name()) or cat.__name__
    footer = f"Try '{name} -h' for more information."
    usage(name, cat.__doc__, footer, cli)
    sys.exit(1)


cli = ShellParser(
    name=cat.__name__,
    description=cat.__doc__,
    params=[
        Param("path", ["-p", "--path"], comb.One(Path), lambda _, b: b),
    ],
    exception_handler=exception_handler,
    function=cat,
)

if __name__ == "__main__":
    names = cli(sys.argv[1:])
    try:
        print(names.bind(cat))
    except Exception as exc:
        print("Something went wrong:", exc)
