from socket import socket
from pydantic import ValidationError
from structlog import get_logger
from dns.name import from_text as dns_from_text

from consulns.daemon.proto import (
    DomainInfo,
    GetAllDomainMetadataParameters,
    GetAllDomainsParameters,
    InitializeParameters,
    ListParameters,
    LookupParameters,
    Query,
    Response,
    QueryAdapter,
    ZoneKind,
)
from consulns.daemon.cache import Cache

dlog = get_logger()
id_cnt = 0


class Handler:
    __id_cnt = 0

    def __init__(self, sock: socket, store: Cache) -> None:
        self._id = Handler.__id_cnt
        Handler.__id_cnt += 1

        self._log = dlog.bind(conn_id=self._id)
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
                        self.reply(Response(result=False))
                        continue

                    try:
                        self.handle_query(query)
                    except Exception as err:
                        self._log.error(
                            "error while handling query", query=query, err=err
                        )
                        from rich.console import Console

                        Console().print_exception(show_locals=True)
        finally:
            self._log.info("connection closed")
            self._sock.close()

    def reply(self, resp: Response) -> None:
        try:
            self._log.debug("sending response", response=resp)
            json = resp.model_dump_json()
            self._log.debug("sending raw response", raw_response=json)
            self._sock.sendall(json.encode("utf-8"))
        except Exception as err:
            self._log.error(
                "error while serializing response", response=resp, err=err
            )

    def handle_query(self, msg: Query) -> None:
        self._log.debug("received query", msg=msg)
        match msg.method:
            case "initialize":
                self.handle_initialize(msg.parameters)
            case "getAllDomains":
                self.handle_get_all_domains(msg.parameters)
            case "getAllDomainMetadata":
                self.handle_get_all_domain_metadata(msg.parameters)
            case "lookup":
                self.handle_lookup(msg.parameters)
            case "list":
                self.handle_list(msg.parameters)
            case _:
                assert False

    def handle_initialize(self, _: InitializeParameters):
        self.reply(Response(result=True))

    def handle_get_all_domains(self, params: GetAllDomainsParameters) -> None:
        domains = [
            DomainInfo(
                id=i,
                zone=zone.name.to_text(),
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

    def handle_get_all_domain_metadata(
        self, params: GetAllDomainMetadataParameters
    ) -> None:
        # TODO: get/set domain metadata
        self.reply(Response(result=[]))

    def handle_lookup(self, params: LookupParameters) -> None:
        self._log.info(
            "performing lookup", qtype=params.qtype, qname=params.qname
        )
        qname = dns_from_text(params.qname)
        if params.zone_id is not None and params.zone_id != -1:
            zone = self._store.zone_by_id(params.zone_id)
        else:
            _, zone = self._store.zone_by_qname(qname)

        if zone is None:
            self._log.warning(
                "lookup is requesting domain in missing zone", domain=qname
            )
            self.reply(Response(result=[]))
            return

        records = zone.lookup(params.qtype, qname)

        self.reply(Response(result=list(records)))

    def handle_list(self, params: ListParameters) -> None:
        zonename = dns_from_text(params.zonename)
        self._log.info(
            "listing zone", zone=zonename, domain_id=params.domain_id
        )

        # TODO: figure out whether `domain_id` is the zone id. PDNS has
        # inconsistent naming all over the place.
        if params.domain_id is not None and params.domain_id != -1:
            zone = self._store.zone_by_id(params.domain_id)
        else:
            _, zone = self._store.zone_by_qname(zonename)

        if zone is None:
            self._log.warning("attempted to list missing zone", zone=zonename)
            self.reply(Response(result=[]))
            return

        self.reply(Response(result=[record for _, record in zone.records()]))

    # DNSSEC handlers
    def handle_get_domain_keys(self, params: GetDomainKeysParams) -> None:
        pass
