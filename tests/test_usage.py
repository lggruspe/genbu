# pylint: disable=disallowed-name
"""Test genbu.usage."""

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
