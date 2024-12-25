from collections import defaultdict
from typing import Dict, Iterator, List, Tuple

from consul import Consul as ConsulClient
from dns.name import Name as DNSName, from_text as dns_from_text

from consulns.daemon.config import Config
from consulns.daemon.proto import QType, RecordInfo
from consulns.store.zone import Zone
from consulns.store.record import Record, RecordType
from consulns.store.consul import Consul

qtype2rtype = {
    QType.A: RecordType.A,
    QType.AAAA: RecordType.AAAA,
    QType.CNAME: RecordType.CNAME,
    QType.MX: RecordType.MX,
    QType.NS: RecordType.NS,
}

rtype2qtype = {
    RecordType.A: QType.A,
    RecordType.AAAA: QType.AAAA,
    RecordType.CNAME: QType.CNAME,
    RecordType.MX: QType.MX,
    RecordType.NS: QType.NS,
}


class CachedZone:
    def __init__(
        self, zone: Zone, records: Dict[DNSName, List[Record]]
    ) -> None:
        self._zone = zone
        self._records = records

    @property
    def zone(self) -> Zone:
        return self._zone

    @property
    def soa(self) -> RecordInfo:
        qname_str = self._zone.name.to_text()
        return RecordInfo(
            qname=qname_str,
            qtype=QType.SOA,
            # TODO: properly do the SOA record
            content=f"ns1.{qname_str} root.{qname_str} {self._zone.serial} 7200 3600 1209600 3600",
            ttl=300,
            auth=True,
        )

    @property
    def raw_records(self) -> Iterator[Tuple[DNSName, Record]]:
        return (
            (domain, record)
            for domain, records in self._records.items()
            for record in records
        )

    def _record_info(self, domain: DNSName, record: Record) -> RecordInfo:
        return RecordInfo(
            qname=domain.to_text(),
            qtype=rtype2qtype[record.record_type],
            content=str(record.value),
            ttl=record.ttl,
            # Figure out what `auth` exactly is.
            # If it just means "authoritative", then we're always authoritative
            # for these records.
            auth=True,
        )

    @property
    def records(self) -> Iterator[Tuple[DNSName, RecordInfo]]:
        yield (self._zone.name, self.soa)
        for domain, record in self.raw_records:
            yield domain, self._record_info(domain, record)

    def lookup(self, qtype: QType, qname: DNSName) -> Iterator[RecordInfo]:
        # Handle queries such as *.example.com
        sub, _ = qname.split(1)
        if sub == "*":
            records = self.raw_records

        records = map(lambda r: (qname, r), self._records[qname])

        def accept_qtype(r: Record) -> bool:
            if qtype == QType.ANY:
                return True
            else:
                rtype = qtype2rtype[qtype]
                return r.record_type == rtype

        # Return SOA on ANY/SOA on @
        if qname == self._zone.name and (
            qtype == QType.ANY or qtype == QType.SOA
        ):
            yield self.soa

        if qtype == QType.SOA:
            # We are done already
            return

        filtered = (
            (domain, record)
            for domain, record in records
            if accept_qtype(record)
        )
        for domain, record in filtered:
            yield self._record_info(domain, record)


class Cache:
    _czs: Dict[DNSName, Tuple[int, CachedZone]]
    _czs_by_id: Dict[int, CachedZone]

    def __init__(self, config: Config) -> None:
        self._config = config
        self.load()

    def load(self) -> None:
        # TODO: add a reset method to Consul, so we don't need to re-instantiate
        self._consul = Consul(
            ConsulClient(
                scheme=self._config.consul_addr.scheme,
                host=self._config.consul_addr.host,
                port=self._config.consul_addr.port,
            )
        )
        # TODO: add zones for reverse domains
        self._czs = {}
        self._czs_by_id = {}

        for i, zone in enumerate(self._consul.zones):
            records = defaultdict(lambda: [])
            cz = CachedZone(zone, records)

            self._czs[zone.name] = (i, cz)
            self._czs_by_id[i] = cz
            for record in zone.records:
                if record.record != "@":
                    sub = dns_from_text(record.record, origin=None)
                    domain = sub.concatenate(zone.name)
                else:
                    domain = zone.name
                # TODO: handle CONSUL records
                records[domain].append(record)

        # TODO: Get reverse IPs (need some information on netmask)
        # records = (record for records in self._records.values() for record in records)
        # ips = []
        # for record in records:
        #     if record.record_type != RecordType.A or record.record_type != RecordType.AAAA:
        #         continue

    @property
    def zones(self) -> Iterator[Tuple[int, CachedZone]]:
        for cz in self._czs.values():
            yield cz

    def zone_by_id(self, id: int) -> CachedZone | None:
        if id in self._czs_by_id:
            return self._czs_by_id[id]

        return None

    def zone_by_qname(
        self, domain: DNSName, exact: bool = False
    ) -> Tuple[int, CachedZone | None]:
        best_cz = None
        best_i = -1
        best_len = 0
        for zdom, (i, cz) in self._czs.items():
            domain_match = (exact and zdom == domain) or (
                not exact and domain.is_subdomain(zdom)
            )
            if domain_match and len(zdom) > best_len:
                best_cz = cz
                best_i = i
                best_len = len(zdom)

        return best_i, best_cz
