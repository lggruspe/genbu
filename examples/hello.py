import sys
from tortoise import (
    CliException, Param, ParamsParser, forward, combinators as comb, usage
)


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
    try:
        optargs = cli(sys.argv[1:])
        print(forward(optargs, hello))
    except CliException:
        footer = f"Try '{hello.__name__} -h' for more information."
        usage(hello.__name__, hello.__doc__, footer, cli)
