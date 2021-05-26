from pathlib import Path
import sys
from tortoise import (
    CliException, Param, ShellParser, forward, combinators as comb, usage
)


def cat(path: Path) -> str:
    """Concatenate contents of path to stdout."""
    return path.read_text()


def exception_handler(exc: CliException):
    footer = f"Try '{cat.__name__} -h' for more information."
    usage(cat.__name__, cat.__doc__, footer, cli)
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
    _, optargs = cli(sys.argv[1:])
    try:
        print(forward(optargs, cat))
    except Exception as exc:
        print("Something went wrong:", exc)
