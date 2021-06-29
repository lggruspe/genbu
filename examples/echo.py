from genbu import Genbu


def echo(*args: str) -> str:
    """Echo strings."""
    if not args:
        return "Usage: echo [--args <str>...]"
    return " ".join(args)


cli = Genbu(echo)

if __name__ == "__main__":
    print(cli.run())
