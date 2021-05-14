from functools import partial
import sys
from tortoise import Merger, Reader, forward, combinators as comb
from tortoise.cli import make_cli


def hello(*names: str, greeting: str = "Hello") -> str:
    """Say hello."""
    if not names:
        names = ("stranger",)
    return "{}, {}!".format(greeting, ", ".join(names))


reader = Reader("g", g=1, greeting=1)
merger = Merger()
merger.add("greeting", "g", using=lambda _, b: b)

cli = make_cli(
    reader.read,
    merger.merge,
    partial(comb.parse_opts, greeting=comb.one(str)),
    partial(comb.parse_args, names=comb.repeat(comb.one(str), then=tuple)),
)
optargs = cli(sys.argv[1:])
print("optargs", optargs)
print(forward(optargs, hello))
