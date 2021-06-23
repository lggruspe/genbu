genbu
=====

![GitHub Workflow Status](https://img.shields.io/github/workflow/status/lggruspe/genbu/Python%20package)
[![PyPI](https://img.shields.io/pypi/v/genbu)](https://pypi.org/project/genbu/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/genbu)](https://pypi.org/project/genbu/)
[![GitHub](https://img.shields.io/github/license/lggruspe/genbu)](./LICENSE)

Genbu is a library for creating command-line interfaces using shell
parser combinators and type hints.

Install
-------

```bash
pip install genbu
```

Infer a parameter parser from type hints
----------------------------------------

```python
import typing as t
from genbu.infer import infer_parser

parse = infer_parser(t.Optional[int])

assert parse(["5"]) == 5
assert parse(["-11"]) == -11
assert parse([""]) is None
assert parse(["None"]) is None

try:
    parse(["12.13"])
except ValueError:
    print("not an Optional[int]")

parse_tuple = infer_parser(tuple[float, ...])

assert parse_tuple(["1.5"]) == (1.5,)
assert parse_tuple(["0.0", "4.2", "-1"]) == (0.0, 4.2, -1.0)
assert parse_tuple([]) == ()

try:
    parse(["Hello, world!"])
except ValueError:
    print("not a tuple[float, ...]")
```

License
-------

[MIT](./LICENSE)
