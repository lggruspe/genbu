"""Shell options parser combinators."""

import collections
import dataclasses
import typing as t


@dataclasses.dataclass
class Result:
    """Parse result."""
    value: t.Any
    empty: bool = False


Tokens = collections.deque[str]
ThenFunction = t.Callable[[t.Sequence[t.Any]], t.Any]


@dataclasses.dataclass
class Parser:
    """Shell options parser."""
    function: t.Callable[[Tokens], Result]

    def __call__(self, tokens: Tokens) -> Result:
        """Parse tokens, but consume tokens only on success."""
        copy = tokens.copy()
        result = self.function(copy)  # type: ignore
        while len(copy) < len(tokens):
            tokens.popleft()
        return result


class CantParse(ValueError):
    """Can't parse type from tokens."""


def one(func: t.Callable[[str], t.Any]) -> Parser:
    """Convert string function into an options parser."""
    def parser(tokens: Tokens) -> Result:
        try:
            return Result(func(tokens.popleft()))
        except Exception as exc:
            raise CantParse from exc
    return Parser(parser)


def or_(*parsers: Parser) -> Parser:
    """Run parsers one at a time and return first non-error result."""
    def parser(tokens: Tokens) -> Result:
        for parse in parsers:
            try:
                return parse(tokens)
            except CantParse:
                pass
        raise CantParse
    return Parser(parser)


def and_(*parsers: Parser, then: ThenFunction = list) -> Parser:
    """Run all parsers and fail if any of the parsers fail."""
    def parser(tokens: Tokens) -> Result:
        value = [r.value for p in parsers if not (r := p(tokens)).empty]
        return Result(then(value))
    return Parser(parser)


def repeat(parser: Parser, then: ThenFunction = list) -> Parser:
    """Run parser as many times as needed on tokens."""
    def _parser(tokens: Tokens) -> Result:
        value = []
        length = len(tokens)
        while tokens:
            try:
                result = parser(tokens)
                if not result.empty:
                    value.append(result.value)
            except CantParse:
                break
            if length == len(tokens):
                raise CantParse
            length = len(tokens)
        return Result(then(value))
    _parser.__name__ = "parser"
    return Parser(_parser)


@Parser
def eof(tokens: Tokens) -> Result:
    """Check if there are no tokens left."""
    if tokens:
        raise CantParse
    return Result(None, empty=True)


@Parser
def none(_: Tokens) -> Result:
    """Return None."""
    return Result(None)


@Parser
def bool_(tokens: Tokens) -> Result:
    """Parse into bool."""
    if tokens:
        lower = tokens.popleft().lower()
        if lower in ("1", "t", "true", "y", "yes"):
            return Result(True)
        if lower in ("0", "f", "false", "n", "no"):
            return Result(False)
    raise CantParse


def parse_opts(opts: dict[str, list[str]],
               **parsers: Parser,
               ) -> dict[str, t.Any]:
    """Parse options into dict.

    Just copy option args if no parser is provided for the option.
    """
    result = {}
    for opt, args in opts.items():
        parse = parsers.get(opt)
        if parse is None:
            result[opt] = args
        else:
            result[opt] = parse(collections.deque(args)).value
    return result


def parse_args(args: list[str], **parsers: Parser) -> dict[str, t.Any]:
    """Parse arguments into dict.

    Use parser name as key.
    """
    deque = collections.deque(args)
    return {name: parse(deque).value for name, parse in parsers.items()}
