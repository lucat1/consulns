from typing import cast
from socket import socket, AF_UNIX, SOCK_STREAM
from threading import Thread
from argparse import ArgumentParser
from pathlib import Path
from structlog import get_logger

from consulns.daemon.config import Config
from consulns.daemon.handler import Handler
from consulns.daemon.cache import Cache

log = get_logger()


def daemon() -> None:
    parser = ArgumentParser(
        prog="cnsd",
        description="ConsulNS daemon implementing PowerDNS remote backend",
    )
    parser.add_argument("socket_path", type=Path)
    args = parser.parse_args()
    socket_path = cast(Path, args.socket_path)

    config = Config()
    log.info("loaded config", config=config)
    cache = Cache(config)

    if socket_path.exists():
        log.warning("deleting old socket", path=socket_path)
        socket_path.unlink()

    srv = socket(AF_UNIX, SOCK_STREAM)
    srv.bind(str(socket_path))
    srv.listen()
    log.info("listening on UNIX socket", path=socket_path)

    try:
        while True:
            sock, _ = srv.accept()
            handler = Handler(sock, cache)
            thr = Thread(target=handler.handle)
            thr.daemon = True
            thr.start()
    finally:
        log.info("Shutting down server")
        srv.close()
        socket_path.unlink()
