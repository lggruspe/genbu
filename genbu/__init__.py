"""Genbu CLI."""

from .cli import Genbu, MissingArgument, default_error_handler
from .cli.normalize import AmbiguousOption, UnknownOption
from .combinators import CantParse
from .exceptions import CLError
from .infer import UnsupportedType, infer_parser
from .infer_params import infer_params_from_signature as infer_params
from .params import InvalidOption, Param
from .usage import usage

__all__ = [
    "AmbiguousOption",
    "CLError",
    "CantParse",
    "Genbu",
    "InvalidOption",
    "MissingArgument",
    "Param",
    "UnknownOption",
    "UnsupportedType",
    "default_error_handler",
    "infer_params",
    "infer_parser",
    "usage",
]
