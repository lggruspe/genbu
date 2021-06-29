# pylint: disable=disallowed-name
"""Test genbu.usage."""

import string

from genbu import Genbu, Param, combinators as comb, usage


def callback() -> None:
    """Does nothing."""


def test_usage_with_params() -> None:
    """usage(...) should contain description of options."""
    cli = Genbu(
        name="test-cli",
        description="Test Genbu.",
        callback=callback,
        params=[
            Param("foo", parser=comb.One(str)),
            Param("aaa", ["-a", "--aaa"], comb.One(str),
                  description="Set aaa."),
            Param("ahh", ["--ahh"], comb.One(str),
                  description="Set ahh."),
            Param("baa", ["-b", "--baa"], comb.One(str),
                  description="Set baa."),
            Param("bar", ["--bar"], comb.One(str)),
            Param("baz", ["--baz"], comb.One(str)),
        ],
    )
    assert usage(cli) == """usage:  test-cli [options] <foo:str>

Test Genbu.

options:
    -a, --aaa <str>
        Set aaa.

    --ahh <str>
        Set ahh.

    -b, --baa <str>
        Set baa.

    --bar <str>
    --baz <str>"""


def test_usage_with_subcommands() -> None:
    """usage(...) should contain description of subcommands."""
    bar = Genbu(
        name="bar",
        description="Bar subcommand",
        callback=callback,
    )
    baz = Genbu(
        name="baz",
        description="Baz subcommand",
        callback=callback,
    )
    foo = Genbu(
        name="foo",
        description="Foo command.",
        callback=callback,
        subparsers=[bar, baz],
    )
    assert usage(foo) == """usage:  foo <command> ...

Foo command.

commands:
    bar, baz

    bar     Bar subcommand
    baz     Baz subcommand"""


def test_usage_with_header_and_footer() -> None:
    """usage(...) should contain header and footer."""
    cli = Genbu(
        name="test-cli",
        description="Test Genbu",
        callback=callback,
    )
    assert usage(cli, header="Hello.", footer="Bye.") == """usage:  test-cli

Hello.

Bye."""


def test_usage_with_multiple_examples() -> None:
    """usage(...) should have properly indented example lines."""
    bar = Genbu(
        name="bar",
        description="Bar subcommand",
        callback=callback,
    )
    foo = Genbu(
        name="foo",
        description="Foo command.",
        params=[
            Param("help_", ["-?", "-h"], parser=comb.Emit(True)),
        ],
        callback=callback,
        subparsers=[bar],
    )
    assert usage(foo).startswith("""usage:  foo [options]
        foo <command> ...""")


def test_usage_with_custom_arg_descriptions() -> None:
    """usage(...) should use custom description instead of default one."""
    cli = Genbu(
        name="test-cli",
        description="Test Genbu",
        params=[
            Param("default", ["-a"], parser=comb.Repeat(comb.One(int))),
            Param(
                "custom",
                ["-b"],
                parser=comb.Repeat(comb.One(int)),
                arg_description="custom-arg-description",
            )
        ],
        callback=callback,
    )
    assert usage(cli) == """usage:  test-cli [options]

Test Genbu

options:
    -a <[int...]>
    -b custom-arg-description"""


def test_usage_with_really_long_list_of_commands() -> None:
    """usage(...) should break line."""
    def make_subcli(name: str) -> Genbu:
        return Genbu(
            name=name,
            description="Test subcommand",
            callback=callback,
        )

    cli = Genbu(
        name="test-cli",
        description="Test Genbu",
        subparsers=[make_subcli(3*a) for a in string.ascii_lowercase],
        callback=callback,
    )

    assert usage(cli).startswith("""usage:  test-cli <command> ...

Test Genbu

commands:
    aaa, bbb, ccc, ddd, eee, fff, ggg, hhh, iii, jjj, kkk, lll, mmm,
    nnn, ooo, ppp, qqq, rrr, sss, ttt, uuu, vvv, www, xxx, yyy, zzz

    aaa""")


def test_usage_on_subparser() -> None:
    """usage(...) example line should contain subcommand name."""
    bar = Genbu(
        name="bar",
        description="Bar subcommand",
        callback=callback,
    )
    Genbu(
        name="foo",
        description="Foo command",
        callback=callback,
        subparsers=[bar],
    )

    assert usage(bar).startswith("""usage:  foo bar

Bar subcommand""")
