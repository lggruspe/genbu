import sys
from genbu import Genbu, Param, combinators as comb, infer_parser, usage


def hello(*names: str, greeting: str = "Hello") -> str:
    """Say hello."""
    if not names:
        names = ("stranger",)
    return "{}, {}!".format(greeting, ", ".join(names))


cli = Genbu(
    hello,
    params=[
        Param("greeting", ["-g", "--greeting"], comb.One(str)),
        Param("names", parser=infer_parser(tuple[str, ...])),
        Param(
            "help_",
            ["-?", "-h", "--help"],
            comb.Emit(True),
            aggregator=lambda _: sys.exit(usage(cli))
        ),
    ],
)

if __name__ == "__main__":
    print(cli.run())
