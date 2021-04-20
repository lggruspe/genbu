infer-parser
============

infer-parser is a Python library for inferring parsers from type annotations.

Example
-------

```python
from typing import Optional
from infer_parser import infer, CantParse

parse = infer(Optional[float])

assert parse("1.5") == 1.5
assert parse("") is None
assert parse("None") is None
assert isinstance(parse("Hello, world!"), CantParse)
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
