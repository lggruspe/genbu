infer-parser
============

![GitHub Workflow Status](https://img.shields.io/github/workflow/status/lggruspe/infer-parser/Python%20package)
[![PyPI](https://img.shields.io/pypi/v/infer_parser)](https://pypi.org/project/infer_parser/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/infer_parser)](https://pypi.org/project/infer_parser/)
[![GitHub](https://img.shields.io/github/license/lggruspe/infer-parser)](./LICENSE)

infer-parser is a Python library for making shell argument parsers from type hints.

Install
-------

```bash
pip install infer-parser
```

Example
-------

```python
import typing as t
from infer_parser import make_parser

parse = make_parser(t.Optional[int])

assert parse(["5"]) == 5
assert parse(["-11"]) == -11
assert parse([""]) is None
assert parse(["None"]) is None

try:
    parse(["12.13"])
except ValueError:
    print("not an Optional[int]")

parse_tuple = make_parser(tuple[float, ...])

assert parse_tuple(["1.5"]) == (1.5,)
assert parse_tuple(["0.0", "4.2", "-1"]) == (0.0, 4.2, -1.0)
assert parse_tuple([]) == ()

try:
    parse(["Hello, world!"])
except ValueError:
    print("not a tuple[float, ...]")
```

Limitations
-----------

infer-parser cannot always infer a parser.

```python
import typing as t
from infer_parser import make_parser

try:
    make_parser(t.Callable[..., int])
except TypeError:
    print("not supported")
```

License
-------

[MIT](./LICENSE).
