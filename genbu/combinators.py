"""Option arguments parser combinators."""

import abc
import typing as t

from .exceptions import CLError


class Result:  # pylint: disable=too-few-public-methods
    """Parse result."""
    def __init__(self, value: t.Any, empty: bool = False):
        self.value = value
        self.empty = empty


Tokens = t.Deque[str]
ThenFunction = t.Callable[[t.Sequence[t.Any]], t.Any]


class Parser(abc.ABC):
    """Shell options parser."""
    def __call__(self, tokens: Tokens) -> Result:
        """Parse tokens, but consume tokens only on success."""
        copy = tokens.copy()
        result = self.parse(copy)
        while len(copy) < len(tokens):
            tokens.popleft()
        return result

    @abc.abstractmethod
    def parse(self, tokens: Tokens) -> Result:
        """Abstract parse method."""

    def pretty(self, template: str = "<{}>") -> str:
        """Pretty print Parser type."""
        return template.format(str(self))

    @abc.abstractmethod
    def __str__(self) -> str:
        """Parser 'type' as string."""


class CantParse(CLError):
    """Can't parse type from tokens."""
    def __init__(self, parser: Parser, tokens: t.Sequence[str]):
        super().__init__(self)
        self.parser = parser
        self.tokens = tuple(tokens)

    def __str__(self) -> str:
        tokens = ' '.join(self.tokens)
        return f"cannot parse {self.parser} from {tokens!r}"


class One(Parser):
    """Single token parser."""
    def __init__(self, func: t.Callable[[str], t.Any]):
        self.func = func

    def __str__(self) -> str:
        return self.func.__name__

    def parse(self, tokens: Tokens) -> Result:
        """Parse tokens using string function (self.func)."""
        try:
            return Result(self.func(tokens.popleft()))
        except Exception as exc:
            raise CantParse(self, tokens) from exc


class Lit(Parser):
    """Literal parser.

    Type of value should implement __str__.
    """
    def __init__(self, value: t.Any):
        self.value = value

    def __str__(self) -> str:
        return str(self.value)

    def parse(self, tokens: Tokens) -> Result:
        """Parse value."""
        if not tokens or tokens[0] != str(self.value):
            raise CantParse(self, tokens)
        tokens.popleft()
        return Result(self.value)


class Or(Parser):
    """Union of Parsers."""
    def __init__(self, *parsers: Parser):
        self.parsers = parsers

    def __str__(self) -> str:
        optional = any(isinstance(p, Emit) for p in self.parsers)
        parsers = tuple(p for p in self.parsers if not isinstance(p, Emit))
        if len(parsers) == 0:
            return "''"
        if len(parsers) == 1:
            expr = str(parsers[0])
            return expr if not optional else f"[{expr}]"
        exprs = " | ".join(map(str, parsers))
        return f"[{exprs}]" if optional else f"({exprs})"

    def parse(self, tokens: Tokens) -> Result:
        """Run parsers one at a time and return first non-error result."""
        for parse in self.parsers:
            try:
                return parse(tokens)
            except CantParse:
                pass
        raise CantParse(self, tokens)


class And(Parser):
    """Concatenation of Parsers (separated by spaces)."""
    def __init__(self, *parsers: Parser, then: ThenFunction = list):
        self.parsers = parsers
        self.then = then

    def __str__(self) -> str:
        parsers = tuple(p for p in self.parsers if not isinstance(p, Emit))
        if len(parsers) == 0:
            return "''"
        if len(parsers) == 1:
            return str(parsers[0])
        return "({})".format(" ".join(map(str, parsers)))

    def parse(self, tokens: Tokens) -> Result:
        """Run all parsers and fail if any of the parsers fail."""
        results = (p(tokens) for p in self.parsers)
        values = [r.value for r in results if not r.empty]
        return Result(self.then(values))


class Repeat(Parser):
    """Repeated Parser."""
    def __init__(self, parser: Parser, then: ThenFunction = list):
        self.parser = parser
        self.then = then

    def __str__(self) -> str:
        expr = str(self.parser)
        if isinstance(self.parser, Emit) or expr == "''":
            return "''"
        return f"[{self.parser!s}...]"

    def parse(self, tokens: Tokens) -> Result:
        """Run parser as many times as needed on tokens."""
        value = []
        length = len(tokens)
        while tokens:
            try:
                result = self.parser(tokens)
                assert not result.empty
                value.append(result.value)
            except CantParse:
                break
            if length == len(tokens):  # Avoid infinite loop
                break
            length = len(tokens)
        return Result(self.then(value))


class Emit(Parser):
    """Empty token parser that emits value."""
    def __init__(self, value: t.Any):
        self.value = value

    def __str__(self) -> str:
        return "''"

    def parse(self, tokens: Tokens) -> Result:
        """Just emit value."""
        return Result(self.value)


class Eof(Parser):
    """EOF checker."""
    def __str__(self) -> str:
        return "''"

    def parse(self, tokens: Tokens) -> Result:
        """Check if there are no tokens left."""
        if tokens:
            raise CantParse(self, tokens)
        return Result(None, empty=True)


class Bool(Parser):
    """Bool Parser."""
    def __str__(self) -> str:
        return "bool"

    def parse(self, tokens: Tokens) -> Result:
        """Parse into bool."""
        if tokens:
            lower = tokens.popleft().lower()
            if lower in ("1", "t", "true", "y", "yes"):
                return Result(True)
            if lower in ("0", "f", "false", "n", "no"):
                return Result(False)
        raise CantParse(self, tokens)
