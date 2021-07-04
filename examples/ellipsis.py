import sys
from genbu import Genbu, Param, combinators as comb, usage


def ellipsis(n: int) -> str:
    return n * "*"


cli = Genbu(ellipsis, params=[
    "...",
    Param(
        dest="_",
        optargs=["-?", "-h", "--help"],
        parser=comb.Emit(True),
        aggregator=lambda _: sys.exit(usage(cli)),
    ),
])


if __name__ == "__main__":
    print(cli.run())
