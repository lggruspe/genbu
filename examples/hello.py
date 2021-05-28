import sys
from tortoise import (
    CliException, Param, ShellParser, combinators as comb, usage
)


def hello(*names: str, greeting: str = "Hello") -> str:
    """Say hello."""
    if not names:
        names = ("stranger",)
    return "{}, {}!".format(greeting, ", ".join(names))


def exception_handler(cli: ShellParser, exc: CliException):
    name = " ".join(cli.complete_name()) or hello.__name__
    footer = f"Try '{name} -h' for more information."
    usage(name, hello.__doc__, footer, cli)
    sys.exit(1)


cli = ShellParser(
    name=hello.__name__,
    description=hello.__doc__,
    params=[
        Param("greeting", ["-g", "--greeting"], comb.One(str), lambda _, b: b),
        Param("names", parse=comb.Repeat(comb.One(str), then=tuple)),
    ],
    exception_handler=exception_handler,
    function=hello,
)

if __name__ == "__main__":
    names = cli(sys.argv[1:])
    print(names.bind(hello))
