import sys
from genbu import Genbu, Param, combinators as comb, usage
from examples import add, cat, echo, hello, simple


def show_usage(cli: Genbu, error: bool = False):
    name = " ".join(cli.complete_name()) or "cli"
    footer = f"Try '{name} -h' for more information."
    _usage = usage(cli, "Genbu CLI example with subcommands.", footer)
    if error:
        sys.exit(_usage)
    print(_usage)
    sys.exit(0)


cli = Genbu(
    name=sys.argv[0],
    description="router example",
    params=[
        Param(
            "help",
            ["-h", "--help"],
            parser=comb.Emit(True),
            aggregator=lambda _: show_usage(cli),
        ),
    ],
    subparsers=[add.cli, cat.cli, echo.cli, hello.cli, simple.cli],
    callback=lambda: show_usage(cli),
    error_handler=lambda cli, exc: show_usage(cli, error=True),
)


if __name__ == "__main__":
    try:
        print(cli.run())
    except Exception as exc:
        print("something went wrong:", exc)
