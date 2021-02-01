from climates import Climate

def hello(name="world"):
    """Say hello."""
    print(f"Hello, {name}!")

def bye(name=None):
    """Say bye."""
    if name:
        print(f"Bye-bye, {name}.")
    else:
        print("Bye-bye.")

cli = Climate("Hello world app.")
cli.add_commands(hello, bye)
cli.run()
