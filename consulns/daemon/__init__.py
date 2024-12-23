from structlog import get_logger
from sys import argv

log = get_logger()

def daemon():
    sock_path = argv[1]
    log.info("daemon listening on", socket=sock_path)
