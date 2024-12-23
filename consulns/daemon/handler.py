from socket import AddressInfo, socket
from pydantic import ValidationError
from structlog import get_logger

from consulns.daemon.proto import Message, MessageAdapter

dlog = get_logger()
id_cnt = 0

class Handler:
    __id_cnt = 0

    def __init__(self, sock: socket) -> None:
        self.id = Handler.__id_cnt
        Handler.__id_cnt += 1

        self.log = dlog.bind(conn_id=id)
        self.sock = sock

    def handle(self) -> None:
        self.log.info("connection enstablished")
        try:
            with self.sock.makefile('rb') as f:
                while True:
                    raw_msg = f.readline()
                    if raw_msg is None or len(raw_msg) == 0:
                        break
                    self.log.debug("received raw message", raw_msg=raw_msg)
                    try:
                        msg = MessageAdapter.validate_json(raw_msg)
                    except ValidationError as err:
                        self.log.error("invalid message", raw_msg=raw_msg, err=err)
                        continue

                    self.handle_msg(msg)
        finally:
            self.log.info("connection closed")
            self.sock.close()

    def handle_msg(self, msg: Message) -> None:
        self.log.debug("received message", msg=msg)
