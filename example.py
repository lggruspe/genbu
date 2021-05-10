import sys
from tortoise import forward, merge, read, combinators as comb


def hello(*names: str, greeting: str = "Hello") -> str:
    """Say hello."""
    if not names:
        names = ("stranger",)
    return "{}, {}!".format(greeting, ", ".join(names))


opts, args = read(sys.argv[1:], "g", g=1, greeting=1)
opts = merge(opts, "greeting", "g", using=lambda _, b: b)
opts = comb.parse_opts(dict(opts), greeting=comb.one(str))
args = comb.parse_args(args, names=comb.repeat(comb.one(str), then=tuple))
optargs = {**opts, **args}

print("optargs", optargs)
print(forward(optargs, hello))
