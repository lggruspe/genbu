"""Usage strings."""

import shutil
import textwrap
import typing as t

from . import combinators as comb
from .params import Param, ParamsParser
from .subcommands import Router


def wrapped_list(head: str, *items: str) -> str:
    """Return wrapped list of items."""
    max_width = min(70, shutil.get_terminal_size().columns) - 4

    lines = [head]
    for item in items:
        width = len(lines[-1]) + 2 + len(item)
        if width < max_width:
            lines[-1] += f", {item}"
        else:
            lines[-1] += ","
            lines.append(item)
    return textwrap.indent("\n".join(lines), "    ")


def command_block(name: str, commands: dict[str, str]) -> str:
    """Construct commands info string."""
    result = f"{name}:\n{wrapped_list(*commands.keys())}\n\n"
    width = max(len(c) for c in commands)
    width += width % 4
    for command, description in commands.items():
        result += f"    {command.ljust(width)}    {description}\n"
    return result


def render_option(param: Param) -> t.Optional[str]:
    """Render option info string.

    Return None if param is not an option.
    """
    if not param.is_option():
        return None

    flags = ", ".join(
        sorted(param.optargs, key=lambda s: (s.startswith("--"), s))
    )

    arg: t.Optional[str] = param.parse.pretty()
    if isinstance(param.parse, comb.Emit) or arg in ("", "<''>"):
        arg = None
    if param.arg_description is not None:
        arg = param.arg_description

    result = flags
    if arg:
        result += f" {arg}"
    if param.description:
        result += f"\n{textwrap.indent(param.description, '    ')}\n"
    return result


def options_block(*params: Param) -> str:
    """Construct options info block."""
    options = filter(bool, map(render_option, params))

    result = "options:\n"
    for i, option in enumerate(options):
        if option is not None:
            if option.count("\n") > 0 and i > 0:
                result += "\n"
            result += textwrap.indent(option, "    ")
            result += "\n"
    return result.strip()


def usage_example(params_parser: ParamsParser) -> str:
    """Return usage example."""
    args = []
    for param in params_parser.params:
        if not param.is_option():
            args.append(f"<{param.name}:{param.parse!s}>")

    prefix = "[options] " if params_parser.options else ""
    return prefix + " ".join(args)


def render_example_router(program: str, cli: Router) -> str:
    """Render usage example of CLI Router."""
    examples = []
    if cli.takes_params():
        subcommand = cli.get_subcommand(())
        examples.append(usage_example(subcommand.cli))
    if cli.has_subcommands():
        examples.append("<command> ...")

    result = "usage:  "
    for i, example in enumerate(examples):
        if i == 0:
            result += f"{program} {example}\n"
        else:
            result += f"        {program} {example}\n"
    return result.strip()


def render_example(program: str, cli: t.Union[ParamsParser, Router]) -> str:
    """Render usage example."""
    if isinstance(cli, ParamsParser):
        return f"usage: {program} {usage_example(cli)}"
    return render_example_router(program, cli)


def usage(program: str,
          header: str,
          footer: str,
          cli: t.Union[ParamsParser, Router],
          ) -> None:
    """Construct and print usage string."""
    result = render_example(program, cli)
    result += f"\n\n{textwrap.dedent(header.strip())}\n\n"

    if isinstance(cli, ParamsParser):
        result += options_block(*cli.params)
    else:
        assert isinstance(cli, Router)
        if cli.takes_params():
            subcommand = cli.get_subcommand(())
            result += options_block(*subcommand.cli.params)

    result += f"\n\n{textwrap.dedent(footer.strip())}"
    print(result)
