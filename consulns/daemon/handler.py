from socket import socket
from pydantic import ValidationError
from structlog import get_logger

from consulns.daemon.proto import (
    DomainInfo,
    GetAllDomainsParameters,
    InitializeParameters,
    LookupParameters,
    Query,
    Response,
    QueryAdapter,
    ZoneKind,
)
from consulns.daemon.store import Store

dlog = get_logger()
id_cnt = 0


class Handler:
    __id_cnt = 0

    def __init__(self, sock: socket, store: Store) -> None:
        self._id = Handler.__id_cnt
        Handler.__id_cnt += 1

        self._log = dlog.bind(conn_id=id)
        self._sock = sock
        self._store = store

    def handle(self) -> None:
        self._log.info("connection enstablished")
        try:
            with self._sock.makefile("rb") as f:
                while True:
                    raw_query = f.readline()
                    if raw_query is None or len(raw_query) == 0:
                        break
                    self._log.debug("received raw query", raw_msg=raw_query)
                    try:
                        query = QueryAdapter.validate_json(raw_query)
                    except ValidationError as err:
                        self._log.error(
                            "invalid query", raw_msg=raw_query, err=err
                        )
                        continue

                    try:
                        self.handle_query(query)
                    except Exception as err:
                        self._log.error(
                            "error while handling query", query=query, err=err
                        )
        finally:
            self._log.info("connection closed")
            self._sock.close()

    def reply(self, resp: Response) -> None:
        try:
            json = resp.model_dump_json()
            self._sock.sendall(json.encode("utf-8"))
        except Exception as err:
            self._log.error(
                "error while serializing response", response=resp, err=err
            )

    def handle_query(self, msg: Query) -> None:
        self._log.debug("received message", msg=msg)
        match msg.method:
            case "initialize":
                self.handle_initialize(msg.parameters)
            case "getAllDomains":
                self.handle_get_all_domains(msg.parameters)
            case "lookup":
                self.handle_lookup(msg.parameters)
            case _:
                assert False

    def handle_initialize(self, _: InitializeParameters):
        self.reply(Response(result=True))

    def handle_get_all_domains(self, params: GetAllDomainsParameters):
        domains = [
            DomainInfo(
                id=i,
                zone=str(zone.name),
                serial=zone.serial,
                notified_serial=zone.notified_serial,
                last_check=zone.last_check,
                kind=ZoneKind.MASTER,
            )
            for i, zone in self._store.zones
            if params.include_disabled or zone.enabled
        ]
        self._log.info("filtered out domains", domains=domains)
        self.reply(Response(result=domains))

    def handle_lookup(self, params: LookupParameters):
        if params.zone_id is not None and params.zone_id != -1:
            zone = self._store.zone_by_id(params.zone_id)
        else:
            zone = self._store.zone(params.zone_id)

        zone.lookup()
        self.reply(Response(result=True))
