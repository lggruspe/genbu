Climates
========

Command-line interfaces made accessible to even simpletons.

Installation
------------

```bash
pip install climates
```

Usage
-----

```python
# Step 1: import Climate
from climates import Climate
# Step 2: create Climate object
cli = Climate("Hello world app.")
# Step 3: ???
# Step 4: add commands to CLI
cli.add_commands(hello, bye)
# Step 5: run CLI
cli.run()
# Step 6: PROFIT!!!
```

See `example.py` for details.

License
-------

MIT.
