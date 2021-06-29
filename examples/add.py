"""Add items."""

import sys

from genbu import Genbu, Param, combinators as comb, usage


def add(*args: float) -> float:
    """Add items."""
    return sum(args)


cli = Genbu(
    add,
    params=[
        Param("args", parser=comb.Repeat(comb.One(float))),
        Param(
            "_",
            ["-?", "-h", "-H"],
            description="Show help message",
            parser=comb.Emit(True),
            aggregator=lambda _: sys.exit(usage(cli)),
        ),
    ],
)

if __name__ == "__main__":
    print(cli.run())
