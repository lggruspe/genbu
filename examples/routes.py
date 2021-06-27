import sys
from genbu import CLInterface, Param, combinators as comb, usage
from examples import cat, hello


def show_usage(cli: CLInterface, error: bool = False):
    name = " ".join(cli.complete_name()) or "cli"
    footer = f"Try '{name} -h' for more information."
    _usage = usage(cli, "Genbu CLI example with subcommands.", footer)
    if error:
        sys.exit(_usage)
    print(_usage)
    sys.exit(0)


cli = CLInterface(
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
    subparsers=[cat.cli, hello.cli],
    callback=lambda: show_usage(cli),
    error_handler=lambda cli, exc: show_usage(cli, error=True),
)


if __name__ == "__main__":
    try:
        print(cli.run())
    except Exception as exc:
        print("something went wrong:", exc)
