#!/usr/bin/env python
from climates import Climate
from subprocess import run

def dist():
    """Make release."""
    run("python setup.py sdist bdist_wheel", shell=True)
    run("twine upload dist/*", shell=True)

cli = Climate("Dev tools.")
cli.add_commands(dist)
cli.run()
