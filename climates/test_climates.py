"""Test climates."""
from argparse import ArgumentParser
from climates import Climate, microclimate


def test_microclimate(cmd_foo, cmd_bar, cmd_baz):
    """microclimate should insert subcommand into subparser."""
    parser = ArgumentParser()
    subparsers = parser.add_subparsers()
    microclimate(subparsers, "foo", cmd_foo)
    microclimate(subparsers, "bar", cmd_bar)
    microclimate(subparsers, "baz", cmd_baz)
    assert subparsers.choices["foo"].description == "Foo."
    assert subparsers.choices["bar"].description == "Bar."
    assert subparsers.choices["baz"].description == "Baz."


def test_climate():
    """Climate constructor must set description and empty commands."""
    cli = Climate("Test CLI app")
    assert cli.description == "Test CLI app"
    assert not cli.commands


def test_climate_add_commands(cli, cmd_foo, cmd_bar):
    """Climate.add_commands should add function to commands.

    It should use the function's name as key to Climate.commands.
    """
    cmd_baz = cmd_bar
    cli.add_commands(cmd_foo, cmd_baz)
    assert len(cli.commands) == 2
    assert cli.commands["foo"] == cmd_foo
    assert cli.commands["bar"] == cmd_bar


def test_climate_add_commands_with_kwargs(cli, cmd_foo, cmd_bar):
    """Climate.add_commands should add functions in kwargs to commands.

    But it should use the keys in kwargs instead of function.__name__.
    """
    cli.add_commands(cmd_foo, baz=cmd_bar)
    assert len(cli.commands) == 2
    assert cli.commands["foo"] == cmd_foo
    assert cli.commands["baz"] == cmd_bar


def test_climate_to_argparse(cli):
    """Climates.to_argparse should create an ArgumentParser object."""
    assert isinstance(cli.to_argparse(), ArgumentParser)


def test_climate_to_argparse_description():
    """Climates.to_argparse should get description from Climate.description."""
    cli = Climate("Test CLI app")
    parser = cli.to_argparse()
    assert cli.description == parser.description


def test_climate_to_argparse_with_commands(cli, cmd_foo, cmd_bar, cmd_baz):
    """Climates.to_argparse should not crash if there are commands."""
    cli.add_commands(cmd_foo, cmd_bar, cmd_baz)
    cli.to_argparse()


def test_climate_run(cli, cmd_foo, cmd_bar, cmd_baz):
    """Climate.run should invoke command handler specified in options."""
    cli.add_commands(cmd_foo, cmd_bar, cmd_baz)
    res_foo = cli.run(["foo", "1"])
    res_bar = cli.run(["bar", "1", "--b", "2", "3"])
    res_baz = cli.run(["baz", "1", "--b", "2", "3", "--c", "c:4", "d:5",
                       "e:6"])
    assert res_foo == ("foo", "1")
    assert res_bar == ("bar", "1", ("2", "3"))
    assert res_baz == ("baz", "1", ("2", "3"), dict(c="4", d="5", e="6"))
