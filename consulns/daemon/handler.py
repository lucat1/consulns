from socket import socket
from typing import Tuple
from pydantic import ValidationError
from structlog import get_logger
from dns.name import from_text as dns_from_text
from itertools import cycle

from consulns.daemon.proto import (
    AddDomainKeyParameters,
    BeforeAndAfterNames,
    DomainInfo,
    GetAllDomainMetadataParameters,
    GetAllDomainsParameters,
    GetBeforeAndAfterNamesAbsoluteParameters,
    GetDomainInfoParameters,
    GetDomainKeysParameters,
    GetDomainMetadataParameters,
    InitializeParameters,
    ListParameters,
    LookupParameters,
    Query,
    RemoveDomainKeyParameters,
    Response,
    QueryAdapter,
    SetDomainMetadataParameters,
    ZoneKind,
)
from consulns.daemon.cache import Cache, CachedZone

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
            case "getDomainInfo":
                self.handle_get_domain_info(msg.parameters)

            case "lookup":
                self.handle_lookup(msg.parameters)
            case "list":
                self.handle_list(msg.parameters)

            case "getAllDomainMetadata":
                self.handle_get_all_domain_metadata(msg.parameters)
            case "getDomainMetadata":
                self.handle_get_domain_metadata(msg.parameters)
            case "setDomainMetadata":
                self.handle_set_domain_metadata(msg.parameters)

            case "getDomainKeys":
                self.handle_get_domain_keys(msg.parameters)
            case "addDomainKey":
                self.handle_add_domain_key(msg.parameters)
            case "removeDomainKey":
                self.handle_remove_domain_key(msg.parameters)
            case "getBeforeAndAfterNamesAbsolute":
                self.handle_get_before_and_after_names_absolute(msg.parameters)

            # TODO: do we even need to handle transactions?
            case "startTransaction":
                self.reply(Response(result=True))
            case "commitTransaction":
                self.reply(Response(result=True))

            case _:
                assert False

    def handle_initialize(self, _: InitializeParameters):
        self.reply(Response(result=True))

    def handle_get_all_domains(self, params: GetAllDomainsParameters) -> None:
        domains = [
            DomainInfo(
                id=i,
                zone=zone._zone.name.to_text(),
                serial=zone._zone.serial,
                notified_serial=zone._zone.notified_serial,
                last_check=zone._zone.last_check,
                kind=ZoneKind.MASTER,
            )
            for i, zone in self._store.zones
            if params.include_disabled or zone._zone.enabled
        ]
        self._log.info("filtered out domains", domains=domains)
        self.reply(Response(result=domains))

    def handle_get_domain_info(self, params: GetDomainInfoParameters) -> None:
        id, zone = self._get_zone_checked(params.name)
        di = DomainInfo(
            id=id,
            zone=zone._zone.name.to_text(),
            serial=zone._zone.serial,
            notified_serial=zone._zone.notified_serial,
            last_check=zone._zone.last_check,
            kind=ZoneKind.MASTER,
        )
        self.reply(Response(result=di))

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
            self.reply(Response(result=False))
            return

        records = zone.lookup(params.qtype, qname)

        self.reply(Response(result=list(records)))

    def handle_list(self, params: ListParameters) -> None:
        _, zone = self._get_zone_checked(params.zonename)
        self._log.info("listing zone", zone=zone.zone.name)

        self.reply(Response(result=[record for _, record in zone.records]))

    def _get_zone_checked(self, zone: str) -> Tuple[int, CachedZone]:
        zonename = dns_from_text(zone)
        id, z = self._store.zone_by_qname(zonename, exact=True)
        if z is None:
            self._log.warinig("requested missing zone", zone=zonename)
            assert False

        return id, z

    def handle_get_all_domain_metadata(
        self, params: GetAllDomainMetadataParameters
    ) -> None:
        _, cz = self._get_zone_checked(params.name)
        self.reply(Response(result=cz.zone.metadata))

    def handle_get_domain_metadata(
        self, params: GetDomainMetadataParameters
    ) -> None:
        _, cz = self._get_zone_checked(params.name)
        metadata = cz.zone.metadata
        if params.kind not in metadata:
            result = []
        else:
            result = metadata[params.kind]
        self.reply(Response(result=result))

    def handle_set_domain_metadata(
        self, params: SetDomainMetadataParameters
    ) -> None:
        _, cz = self._get_zone_checked(params.name)
        cz.zone.set_metadata(params.kind, params.value)
        self.reply(Response(result=True))

    # DNSSEC handlers

    def handle_get_domain_keys(self, params: GetDomainKeysParameters) -> None:
        _, cz = self._get_zone_checked(params.name)

        self.reply(Response(result=list(cz._zone.keys)))

    def handle_add_domain_key(self, params: AddDomainKeyParameters) -> None:
        _, cz = self._get_zone_checked(params.name)

        cz.zone.add_key(params.key)
        self.reply(Response(result=True))

    def handle_remove_domain_key(
        self, params: RemoveDomainKeyParameters
    ) -> None:
        _, cz = self._get_zone_checked(params.name)

        if not any(key.id == params.id for key in cz.zone.keys):
            self._log.warning(
                "attempted to remove non-existing key", key_id=params.id
            )
            self.reply(Response(result=False))
            return

        cz.zone.remove_key(params.id)
        self.reply(Response(result=True))

    def handle_get_before_and_after_names_absolute(
        self, params: GetBeforeAndAfterNamesAbsoluteParameters
    ) -> None:
        qname = dns_from_text(params.qname, origin=None)
        _, zone = self._store.zone_by_qname(qname)
        if zone is None:
            self._log.warning(
                "could not get before/after for missing zone", qname=qname
            )
            self.reply(Response(result=False))
            return

        records = cycle(zone.records)
        before = None
        for _, record in records:
            cmp = dns_from_text(record.qname).relativize(zone.zone.name)
            if cmp == params.qname and before is not None:
                break

            before = cmp
        _, next_record = next(records)
        after = dns_from_text(next_record.qname).relativize(zone.zone.name)

        self.reply(
            Response(
                result=BeforeAndAfterNames(
                    before=before.to_text() if before is not None else "",
                    after=after.to_text() or "",
                    unhashed="",
                )
            )
        )
