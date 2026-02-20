import os
import uvicorn
import argparse

from oscar.logging import configure_logging


def serve(args: argparse.Namespace) -> None:
    configure_logging()
    uvicorn.run("oscar.main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run and manage the Oscar API and MCP Server",
        epilog="See https://github.com/rotationalio/oscar for more information",
    )

    cmds = {
        "serve": {
            "help": "run the server with uvicorn",
            "func": serve,
            "args": {
                "--host": {
                    "type": str,
                    "default": os.environ.get("OSCAR_HOST", "0.0.0.0"),
                    "help": "host address to bind the server to or $OSCAR_HOST (default: 0.0.0.0)",
                },
                "--port": {
                    "type": int,
                    "default": int(os.environ.get("OSCAR_PORT", "8000")),
                    "help": "port to bind the server to or $OSCAR_PORT (default: 8000)",
                },
                "--reload": {
                    "action": "store_true",
                    "default": False,
                    "help": "enable auto-reload for development",
                },
            }
        }
    }

    subparsers = parser.add_subparsers(dest="command", required=True)
    for name, cmd in cmds.items():
        subparser = subparsers.add_parser(name, help=cmd["help"])
        subparser.set_defaults(func=cmd["func"])
        for pargs, kwargs in cmd["args"].items():
            if isinstance(pargs, str):
                pargs = (pargs,)
            subparser.add_argument(*pargs, **kwargs)

    args = parser.parse_args()
    args.func(args)
