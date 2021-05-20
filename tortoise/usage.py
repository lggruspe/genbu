"""Usage strings."""

import shutil
import textwrap


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


def options_block(*options: tuple[tuple[str, ...], str, str]) -> str:
    """Construct options info string."""
    result = "options:\n"
    for names, args, desc in options:
        if desc:
            result += "\n"
        result += "    , ".join(
            sorted(names, key=lambda s: (s.startswith("--"), s))
        )
        if args:
            result += f" {args}"
        result += "\n"
        if desc:
            result += textwrap.indent(desc, " " * 8) + "\n"
    return result
