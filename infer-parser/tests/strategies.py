# pylint: disable=unsubscriptable-object
"""Strategies for generating type annotations."""

import sys
import typing as t
from hypothesis import strategies as st


def t_lists(arg: t.Any) -> st.SearchStrategy[t.Type[t.List[t.Any]]]:
    """Generate list types."""
    choices = [t.List[arg]]  # type: ignore
    if sys.version_info >= (3, 9):
        choices.append(list[arg])  # type: ignore
    return st.sampled_from(choices)


def t_dicts(key: t.Any, val: t.Any
            ) -> st.SearchStrategy[t.Type[t.Dict[t.Any, t.Any]]]:
    """Generate dict types."""
    choices = [t.Dict[key, val]]  # type: ignore
    if sys.version_info >= (3, 9):
        choices.append(dict[key, val])  # type: ignore
    return st.sampled_from(choices)


def t_tuples(*args: t.Any) -> st.SearchStrategy[t.Type[t.Tuple[t.Any, ...]]]:
    """Generate tuple types."""
    if args == ((),):
        args = ()
    choices = [t.Tuple[args]]
    if sys.version_info >= (3, 9):
        choices.append(tuple[args])  # type: ignore
    return st.sampled_from(choices)  # type: ignore


def t_sequences(arg: t.Any) -> st.SearchStrategy[t.Type[t.Sequence[t.Any]]]:
    """Generate sequence types."""
    return st.one_of(t_lists(arg), t_tuples(arg, ...))
