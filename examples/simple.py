import sys
from genbu import Genbu, Param, combinators as comb, usage

cli = Genbu(
    lambda: print("Hello, world!"),
    params=[
        Param("_", ["-?", "-h", "--help"],
              parser=comb.Emit(True),
              aggregator=lambda _: sys.exit(usage(cli))),
    ],
)

if __name__ == "__main__":
    cli.run()
