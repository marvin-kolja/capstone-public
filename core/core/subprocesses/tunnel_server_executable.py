import logging
import signal
import sys
import asyncio
import argparse

from core.tunnel.server import get_tunnel_server

logger = logging.getLogger(__name__)


async def run_server(port: int):
    server = get_tunnel_server()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: server.stop())

    await server.serve(port)
    await server.await_close()


def main():
    parser = argparse.ArgumentParser(description="Run a tunnel server executable")
    parser.add_argument("port", type=int, help="The port to listen on")
    parser.add_argument(
        "--log-level", type=str, default="INFO", help="The logging level"
    )
    args = parser.parse_args()

    levels = {
        "critical": logging.CRITICAL,
        "error": logging.ERROR,
        "warn": logging.WARNING,
        "warning": logging.WARNING,
        "info": logging.INFO,
        "debug": logging.DEBUG,
    }

    logging.basicConfig(level=levels[args.log_level.lower()])

    asyncio.run(run_server(args.port))


if __name__ == "__main__":
    try:
        main()
    except BaseException as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)
