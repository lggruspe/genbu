from pathlib import Path
import sys
from tortoise import (
    CliException, Param, ParamsParser, forward, combinators as comb, usage
)


def cat(path: Path) -> str:
    """Concatenate contents of path to stdout."""
    return path.read_text()


def exception_handler(exc: CliException):
    footer = f"Try '{cat.__name__} -h' for more information."
    usage(cat.__name__, cat.__doc__, footer, cli)
    sys.exit(1)


cli = ParamsParser(
    [
        Param("path", ["-p", "--path"], comb.One(Path), lambda _, b: b),
    ],
    function=cat,
    exception_handler=exception_handler,
)

if __name__ == "__main__":
    optargs = cli(sys.argv[1:])
    try:
        print(forward(optargs, cat))
    except Exception as exc:
        print("Something went wrong:", exc)
