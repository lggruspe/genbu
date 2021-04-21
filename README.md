infer-parser
============

infer-parser is a Python library for inferring shell parsers from type hints.

Example
-------

```python
from typing import Optional
from infer_parser import infer, CantParse

parse = infer(Optional[int])

assert parse("5") == 5
assert parse("-11") == -11
assert parse("") is None
assert parse("None") is None
assert isinstance(parse("12.13"), CantParse)

parse_tuple = infer(tuple[float, ...])

assert parse_tuple("1.5") == (1.5,)
assert parse_tuple("0.0  4.2 -1") == (0.0, 4.2, -1.0)
assert parse_tuple("") == ()
assert isinstance(parse_tuple("Hello, world!"), CantParse)
```

Limitations
-----------

infer-parser cannot always infer a parser.

```python
from typing import Callable
from infer_parser import infer, CantInfer

parse = infer(Callable[..., int])  # not supported
assert isinstance(parse, CantInfer)
```

License
-------

[MIT](./LICENSE).
