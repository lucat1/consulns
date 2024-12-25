from collections import defaultdict
from datetime import datetime
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
}

rtype2qtype = {
    RecordType.A: QType.A,
    RecordType.AAAA: QType.AAAA,
    RecordType.CNAME: QType.CNAME,
    RecordType.MX: QType.MX,
}


class CachedZone:
    def __init__(
        self, zone: Zone, records: Dict[DNSName, List[Record]]
    ) -> None:
        self._zone = zone
        self._records = records

    @property
    def name(self) -> DNSName:
        return self._zone.name

    @property
    def serial(self) -> int:
        return self._zone.serial

    @property
    def notified_serial(self) -> int:
        return self._zone.notified_serial

    @property
    def enabled(self) -> bool:
        return self._zone.enabled

    @property
    def last_check(self) -> datetime:
        return self._zone.last_check

    def lookup(self, qtype: QType, qname: DNSName) -> Iterator[RecordInfo]:
        # Handle queries such as *.example.com
        sub, _ = qname.split(1)
        if sub == "*":
            records = [
                record
                for records in self._records.values()
                for record in records
            ]

        records = self._records[qname]

        def accept_qtype(r: Record) -> bool:
            if qtype == QType.ANY:
                return True
            else:
                rtype = qtype2rtype[qtype]
                return r.record_type == rtype

        filtered = (record for record in records if accept_qtype(record))

        # Return SOA on ANY on @
        if qname == self.name and qtype == QType.ANY:
            qname_str = self.name.to_text()
            ri = RecordInfo(
                qname=qname_str,
                qtype=QType.SOA,
                # TODO: properly do the SOA record
                content=f"ns1.{qname_str} root.{qname_str} {self.serial} 7200 3600 1209600 3600",
                ttl=300,
            )
            yield ri

        for record in filtered:
            ri = RecordInfo(
                qname=qname.to_text(),
                qtype=rtype2qtype[record.record_type],
                content=str(record.value),
                ttl=record.ttl,
            )
            yield ri


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

    def zone_by_qname(self, domain: DNSName) -> Tuple[int, CachedZone | None]:
        best_cz = None
        best_i = -1
        best_len = 0
        for zdom, (i, cz) in self._czs.items():
            if domain.is_subdomain(zdom) and len(zdom) > best_len:
                best_cz = cz
                best_i = i
                best_len = len(zdom)

        return best_i, best_cz
