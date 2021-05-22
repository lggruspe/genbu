import sys
from tortoise import Param, ParamsParser, forward, combinators as comb


def hello(*names: str, greeting: str = "Hello") -> str:
    """Say hello."""
    if not names:
        names = ("stranger",)
    return "{}, {}!".format(greeting, ", ".join(names))


cli = ParamsParser([
    Param("greeting", ["-g", "--greeting"], comb.One(str), lambda _, b: b),
    Param("names", parse=comb.Repeat(comb.One(str), then=tuple)),
])

if __name__ == "__main__":
    optargs = cli(sys.argv[1:])
    print(forward(optargs, hello))
