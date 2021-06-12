"""Usage strings."""

import shutil
import textwrap
import typing as t

from . import combinators as comb
from .cli import CLInterface
from .params import Param


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


def command_block(group_name: str, parser: CLInterface) -> str:
    """Construct command block for shell parser subcommands."""
    names = parser.subparsers.keys()
    result = f"{group_name}:\n{wrapped_list(*names)}\n\n"
    width = max(len(c) for c in names)
    width += 4 - width % 4  # So that name column is a multiple of 4
    for sub in parser.subparsers.values():
        result += f"    {sub.name.ljust(width)}    {sub.description}\n"
    return result.strip()


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
    for option in options:
        assert option is not None
        result += "{}\n".format(textwrap.indent(option, "    "))
    return result.strip()


def usage_example(parser: CLInterface) -> str:
    """Return usage example for CLInterface."""
    args = [
        f"<{p.name}:{p.parse!s}>" for p in parser.params if not p.is_option()
    ]
    prefix = "[options] " if parser.options else ""
    return (prefix + " ".join(args)).strip()


def render_example(parser: CLInterface) -> str:
    """Render usage examples of CLI with subcommands."""
    examples = []
    if parser.takes_params():
        examples.append(usage_example(parser))
    if parser.has_subcommands():
        examples.append("<command> ...")

    name = " ".join(parser.complete_name())
    result = "usage:  "

    if examples:
        for i, example in enumerate(examples):
            if i == 0:
                result += f"{name} {example}\n"
            else:
                result += f"        {name} {example}\n"
    else:
        result += name
    return result.strip()


def usage(parser: CLInterface,
          header: t.Optional[str] = None,
          footer: t.Optional[str] = None,
          ) -> str:
    """Construct usage string."""
    if header is None:
        header = parser.description

    result = render_example(parser)
    result += f"\n\n{textwrap.dedent(header.strip())}\n\n"
    if parser.takes_params():
        result += options_block(*parser.params)
    if parser.has_subcommands():
        result += command_block("commands", parser)
    if footer is not None:
        result += textwrap.dedent(footer.strip())
    return result
