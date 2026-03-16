"""CLI entry point for KeplAI."""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(prog="keplai", description="KeplAI Knowledge Graph Platform")
    sub = parser.add_subparsers(dest="command")

    # keplai serve
    serve_parser = sub.add_parser("serve", help="Start the KeplAI API server")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    serve_parser.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    serve_parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")

    args = parser.parse_args()

    if args.command == "serve":
        try:
            import uvicorn
        except ImportError:
            print("uvicorn is required. Install with: pip install keplai[api]", file=sys.stderr)
            sys.exit(1)
        uvicorn.run("api.main:app", host=args.host, port=args.port, reload=args.reload)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
