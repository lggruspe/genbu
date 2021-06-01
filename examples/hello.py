import sys
from genbu import Param, ShellParser, combinators as comb, usage


def hello(*names: str, greeting: str = "Hello") -> str:
    """Say hello."""
    if not names:
        names = ("stranger",)
    return "{}, {}!".format(greeting, ", ".join(names))


def main(*names: str, greeting: str = "Hello", help_: bool = False) -> str:
    """Entrypoint to hello."""
    if help_:
        sys.exit(usage(cli))
    return hello(*names, greeting=greeting)


cli = ShellParser(
    name=hello.__name__,
    description=hello.__doc__,
    params=[
        Param("greeting", ["-g", "--greeting"], comb.One(str), lambda _, b: b),
        Param("names", parse=comb.Repeat(comb.One(str), then=tuple)),
        Param("help_", ["-?", "-h", "--help"], comb.Emit(True)),
    ],
    function=main,
)

if __name__ == "__main__":
    names = cli(sys.argv[1:])
    print(names.bind(main))
