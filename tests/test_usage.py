# pylint: disable=disallowed-name
"""Test genbu.usage."""

import string

from genbu import CLInterface, Param, combinators as comb, usage


def callback() -> None:
    """Does nothing."""


def test_usage_with_params() -> None:
    """usage(...) should contain description of options."""
    cli = CLInterface(
        name="test-cli",
        description="Test CLInterface.",
        callback=callback,
        params=[
            Param("foo", parse=comb.One(str)),
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

Test CLInterface.

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
    bar = CLInterface(
        name="bar",
        description="Bar subcommand",
        callback=callback,
    )
    baz = CLInterface(
        name="baz",
        description="Baz subcommand",
        callback=callback,
    )
    foo = CLInterface(
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
    cli = CLInterface(
        name="test-cli",
        description="Test CLInterface",
        callback=callback,
    )
    assert usage(cli, header="Hello.", footer="Bye.") == """usage:  test-cli

Hello.

Bye."""


def test_usage_with_multiple_examples() -> None:
    """usage(...) should have properly indented example lines."""
    bar = CLInterface(
        name="bar",
        description="Bar subcommand",
        callback=callback,
    )
    foo = CLInterface(
        name="foo",
        description="Foo command.",
        params=[
            Param("help_", ["-?", "-h"], parse=comb.Emit(True)),
        ],
        callback=callback,
        subparsers=[bar],
    )
    assert usage(foo).startswith("""usage:  foo [options]
        foo <command> ...""")


def test_usage_with_custom_arg_descriptions() -> None:
    """usage(...) should use custom description instead of default one."""
    cli = CLInterface(
        name="test-cli",
        description="Test CLInterface",
        params=[
            Param("default", ["-a"], parse=comb.Repeat(comb.One(int))),
            Param(
                "custom",
                ["-b"],
                parse=comb.Repeat(comb.One(int)),
                arg_description="custom-arg-description",
            )
        ],
        callback=callback,
    )
    assert usage(cli) == """usage:  test-cli [options]

Test CLInterface

options:
    -a <[int...]>
    -b custom-arg-description"""


def test_usage_with_really_long_list_of_commands() -> None:
    """usage(...) should break line."""
    def make_subcli(name: str) -> CLInterface:
        return CLInterface(
            name=name,
            description="Test subcommand",
            callback=callback,
        )

    cli = CLInterface(
        name="test-cli",
        description="Test CLInterface",
        subparsers=[make_subcli(3*a) for a in string.ascii_lowercase],
        callback=callback,
    )

    assert usage(cli).startswith("""usage:  test-cli <command> ...

Test CLInterface

commands:
    aaa, bbb, ccc, ddd, eee, fff, ggg, hhh, iii, jjj, kkk, lll, mmm,
    nnn, ooo, ppp, qqq, rrr, sss, ttt, uuu, vvv, www, xxx, yyy, zzz

    aaa""")


def test_usage_on_subparser() -> None:
    """usage(...) example line should contain subcommand name."""
    bar = CLInterface(
        name="bar",
        description="Bar subcommand",
        callback=callback,
    )
    CLInterface(
        name="foo",
        description="Foo command",
        callback=callback,
        subparsers=[bar],
    )

    assert usage(bar).startswith("""usage:  foo bar

Bar subcommand""")
