from genbu import CLInterface
from genbu.infer_params import infer_params_from_signature as infer


def echo(*args: str) -> str:
    """Echo strings."""
    if not args:
        return "Usage: echo [--args <str>...]"
    return " ".join(args)


cli = CLInterface(echo, params=infer(echo))

if __name__ == "__main__":
    print(cli.run())
