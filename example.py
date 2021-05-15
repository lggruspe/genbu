import sys
from tortoise import Cli, ParamsParser, Renamer, forward, combinators as comb


def hello(*names: str, greeting: str = "Hello") -> str:
    """Say hello."""
    if not names:
        names = ("stranger",)
    return "{}, {}!".format(greeting, ", ".join(names))


parser = ParamsParser({
    "-g": comb.one(str),
    "--greeting": comb.one(str),
    "names": comb.repeat(comb.one(str), then=tuple),
})

renamer = Renamer()
renamer.add("greeting", "-g", "--greeting", resolve=lambda _, b: b)

cli = Cli(parser, renamer)
optargs = cli(sys.argv[1:])
print("optargs", optargs)
print(forward(optargs, hello))
