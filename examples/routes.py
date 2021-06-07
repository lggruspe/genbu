import sys
from genbu import CLError, CLInterface, Param, combinators as comb, usage
from examples import cat, hello


def show_usage(cli: CLInterface, error: bool = False):
    name = " ".join(cli.complete_name()) or "cli"
    footer = f"Try '{name} -h' for more information."
    _usage = usage(cli, "Genbu CLI example with subcommands.", footer)
    if error:
        sys.exit(_usage)
    print(_usage)
    sys.exit(0)


def error_handler(cli: CLInterface, exc: CLError):
    show_usage(cli, error=True)


cli = CLInterface(
    name=sys.argv[0],
    description="router example",
    params=[
        Param("help", ["-h", "--help"], comb.Emit(True), lambda _, b: b)
    ],
    subparsers=[cat.cli, hello.cli],
    callback=lambda: show_usage(cli),
    error_handler=error_handler,
)


try:
    print(cli(sys.argv[1:]))
except Exception as exc:
    print("something went wrong:", exc)
