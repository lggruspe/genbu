"""Make shell arguments parsers from type hints."""

from genbu.combinators import CantParse, Parser
from ._parsers import UnsupportedType, make_parser


__all__ = ["CantParse", "Parser", "UnsupportedType", "make_parser"]
