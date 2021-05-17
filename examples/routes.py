import sys
from tortoise import Cli, ParamsParser, Renamer, forward, combinators as comb
from tortoise.subcommands import Router

from examples import cat, hello

parser = ParamsParser({
    "-h": comb.none,
    "--help": comb.none,
})

renamer = Renamer()
renamer.add("help", "-h", "--help", resolve=lambda _, b: b)

cli = Cli(parser, renamer)

router = Router()
router.add(cat.cli, "cat")
router.add(hello.cli, "hello")
router.add(cli)


try:
    command, optargs = router(sys.argv[1:])
    function = (
        cat.cat if command == ("cat",) else
        hello.hello if command == ("hello",) else
        lambda: """usage: routes.py (-h | --help | <command> ...)
commands: cat, hello"""
    )
    print(forward(optargs, function))
except Exception as exc:
    sys.exit(f"something went wrong: {exc}")
