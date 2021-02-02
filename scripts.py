#!/usr/bin/env python
from climates import Climate
from subprocess import run


def sh(cmd):
    run(cmd, shell=True)


def init():
    """Initialize repository."""
    sh("pip install -r requirements.txt")


def dist():
    """Make release."""
    sh("python setup.py sdist bdist_wheel")
    sh("twine upload dist/*")


def lint():
    """Run linters."""
    sh("flake8 climates")
    sh("pylint climates -d C0102,C0103")


def test():
    """Run tests."""
    sh("pytest --cov=climates --cov-report=term-missing --cov-fail-under=90"
       "--cov-branch")


if __name__ == "__main__":
    cli = Climate("Dev tools.")
    cli.add_commands(init, dist, lint, test)
    cli.run()
