from pathlib import Path
import sys
import typing as t

from genbu import Param, ShellParser, combinators as comb, usage


def cat(path: Path) -> str:
    """Concatenate contents of path to stdout."""
    return path.read_text()


def main(help_: bool = False, path: t.Optional[Path] = None) -> str:
    """Entrypoint to cat."""
    if help_:
        sys.exit(usage(cli))
    assert path is not None, "missing path"
    return cat(path)


cli = ShellParser(
    name=cat.__name__,
    description=cat.__doc__,
    params=[
        Param("path", ["-p", "--path"], comb.One(Path), lambda _, b: b),
        Param("help_", ["-?", "-h", "--help"], comb.Emit(True)),
    ],
    callback=main,
)

if __name__ == "__main__":
    names = cli(sys.argv[1:])
    try:
        print(names.bind(main))
    except Exception as exc:
        name = " ".join(cli.complete_name())
        print(f"{name}: {exc}\nTry '{name} -h' for more information.")
