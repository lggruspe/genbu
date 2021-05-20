# pylint: disable=too-few-public-methods
"""Shell options parser combinator expressions."""

import typing as t


class Expr:
    """Base expression class."""
    def pretty(self, template: str = "<{}>") -> str:
        """Pretty print expression."""
        return template.format(str(self))


class One(Expr):
    """Single token."""
    def __init__(self, func: t.Callable[[str], t.Any]):
        self.func = func

    def __str__(self) -> str:
        return self.func.__name__


class Or(Expr):
    """Alternate tokens."""
    def __init__(self, *exprs: Expr):
        self.optional = any(isinstance(e, Emit) for e in exprs)
        self.exprs = tuple(e for e in exprs if not isinstance(e, Emit))

    def __str__(self) -> str:
        if len(self.exprs) == 0:
            return "''"
        if len(self.exprs) == 1:
            expr = str(self.exprs[0])
            return expr if not self.optional else f"[{expr}]"
        exprs = " | ".join(map(str, self.exprs))
        return f"[{exprs}]" if self.optional else f"({exprs})"


class And(Expr):
    """Concatenate tokens."""
    def __init__(self, *exprs: Expr):
        self.exprs = tuple(e for e in exprs if not isinstance(e, Emit))

    def __str__(self) -> str:
        if len(self.exprs) == 0:
            return "''"
        if len(self.exprs) == 1:
            return str(self.exprs[0])
        return "({})".format(" ".join(map(str, self.exprs)))


class Repeat(Expr):
    """Repeat tokens."""
    def __init__(self, expr: Expr):
        self.expr = expr

    def __str__(self) -> str:
        expr = str(self.expr)
        if isinstance(self.expr, Emit) or expr == "''":
            return "''"
        return f"[{self.expr!s}...]"


class Emit(Expr):
    """Empty token."""
    def __str__(self) -> str:
        return "''"
