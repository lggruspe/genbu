from climates import Climate


def hello(name="world", /):
    """Say hello."""
    print(f"Hello, {name}!")


def example(a, b=1, /, c=2, *d: int, e=3, **f: int):
    print(repr((a, b, c, d, e, f)))


def bye(name=None):
    """Say bye."""
    if name:
        print(f"Bye-bye, {name}.")
    else:
        print("Bye-bye.")


cli = Climate("Hello world app.")
cli.add_commands(hello, bye, example)
cli.run()
