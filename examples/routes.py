import sys
from tortoise import Param, ParamsParser, forward, combinators as comb
from tortoise.subcommands import Router

from examples import cat, hello

cli = ParamsParser([
    Param("help", ["-h", "--help"], comb.Emit(True), lambda _, b: b)
])

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
