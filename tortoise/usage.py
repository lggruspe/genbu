"""Usage strings."""

import shutil
import textwrap
import typing as t

from . import combinators as comb
from .params import Param, ParamsParser


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


def render_example(program: str, params_parser: ParamsParser) -> str:
    """Render usage example."""
    args = []
    for param in params_parser.params:
        if not param.is_option():
            args.append(f"<{param.name}:{param.parse!s}>")

    result = f"usage: {program} "
    if params_parser.options:
        result += "[options]"
    if args:
        result += " "
        result += " ".join(args)
    return result


def usage(program: str, description: str, params_parser: ParamsParser) -> None:
    """Construct and print usage string."""
    result = render_example(program, params_parser)
    result += f"\n\n{textwrap.dedent(description.strip())}\n\n"
    result += options_block(*params_parser.params)
    print(result)
