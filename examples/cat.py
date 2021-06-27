from pathlib import Path
import sys

from genbu import CLInterface, Param, combinators as comb, usage


def cat(path: Path) -> str:
    """Concatenate contents of path to stdout."""
    return path.read_text()


cli = CLInterface(
    cat,
    params=[
        Param("path", ["-p", "--path"], comb.One(Path)),
        Param(
            "help_",
            ["-?", "-h", "--help"],
            comb.Emit(True),
            aggregator=lambda _: sys.exit(usage(cli)),
        ),
    ],
)

if __name__ == "__main__":
    try:
        print(cli.run())
    except Exception as exc:
        name = " ".join(cli.complete_name())
        print(f"{name}: {exc}\nTry '{name} -h' for more information.")
