"""Make shell arguments parsers from type hints."""

from ._parsers import CantParse, Parser, UnsupportedType, make_parser


__all__ = ["CantParse", "Parser", "UnsupportedType", "make_parser"]
