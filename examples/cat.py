from pathlib import Path
import sys
from tortoise import Cli, ParamsParser, forward, Renamer, combinators as comb


def cat(path: Path) -> str:
    """Concatenate contents of path to stdout."""
    return path.read_text()


parser = ParamsParser({
    "-p": comb.One(Path),
    "--path": comb.One(Path),
})

renamer = Renamer()
renamer.add("path", "-p", "--path", resolve=lambda _, b: b)

cli = Cli(parser, renamer)

if __name__ == "__main__":
    optargs = cli(sys.argv[1:])
    print(forward(optargs, cat))
