from pathlib import Path
import sys
from tortoise import Param, ParamsParser, forward, combinators as comb


def cat(path: Path) -> str:
    """Concatenate contents of path to stdout."""
    return path.read_text()


cli = ParamsParser([
    Param("path", ["-p", "--path"], comb.One(Path), lambda _, b: b),
])

if __name__ == "__main__":
    optargs = cli(sys.argv[1:])
    print(forward(optargs, cat))
