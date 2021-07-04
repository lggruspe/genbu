genbu
=====

![GitHub Workflow Status](https://img.shields.io/github/workflow/status/lggruspe/genbu/Python%20package)
[![PyPI](https://img.shields.io/pypi/v/genbu)](https://pypi.org/project/genbu/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/genbu)](https://pypi.org/project/genbu/)
[![GitHub](https://img.shields.io/github/license/lggruspe/genbu)](./LICENSE)

Genbu is a library for creating composable command-line interfaces.

Features
--------

- Infer shell arguments parser from type hints.
- Override inferred parsers using shell parser combinators.
- Compose command-line interfaces declaratively (subcommands).
- Dispatch automatically to the appropriate command callback.
- Generate usage messages by using `genbu.usage`.

Install
-------

```bash
pip install genbu
```

Usage
-----

```python
# hello.py
from genbu import Genbu

print(Genbu(lambda name: f"Hello, {name}!").run())
# Usage example: python hello.py --name "world"
```

See [examples](./examples/).

License
-------

[MIT](./LICENSE)
