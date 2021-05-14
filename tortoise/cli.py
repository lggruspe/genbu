"""CLI object."""

import typing as t


Opts = list[tuple[str, list[str]]]
Args = list[str]
Optargs = dict[str, t.Any]
Read = t.Callable[[t.Sequence[str]], tuple[Opts, Args]]
Merge = t.Callable[[Opts], Opts]
ParseOpts = t.Callable[[dict[str, list[str]]], dict[str, t.Any]]
ParseArgs = t.Callable[[list[str]], dict[str, t.Any]]
Cli = t.Callable[[t.Sequence[str]], Optargs]


def make_cli(read: Read,
             merge: Merge,
             parse_opts: ParseOpts,
             parse_args: ParseArgs,
             ) -> Cli:
    """Create Cli callable (argv -> optargs)."""
    def cli(argv: t.Sequence[str]) -> Optargs:
        opts: t.Any
        args: t.Any
        opts, args = read(argv)
        opts = merge(opts)
        opts = parse_opts(dict(opts))
        args = parse_args(args)
        return {**opts, **args}
    return cli
