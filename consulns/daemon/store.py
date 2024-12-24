from collections import defaultdict
from typing import Dict, Iterator, List, Tuple

from consul import Consul as ConsulClient
from dns.name import Name as DNSName, from_text as dns_from_text

from consulns.daemon.config import Config
from consulns.store.zone import Zone
from consulns.store.record import Record
from consulns.store.consul import Consul

class Store:
    _zones_by_id: Dict[int, Zone]
    _zones: Dict[DNSName, Tuple[int, Zone]]
    _records: Dict[DNSName, List[Record]]

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
        self._zones = {}
        self._records = defaultdict(lambda: [])
        for i, zone in enumerate(self._consul.zones):
            self._zones[zone.name] = (i, zone)
            self._zones_by_id[i] = zone
            for record in zone.records:
                sub = dns_from_text(record.record)
                domain = sub.concatenate(zone.name)
                self._records[domain].append(record)

        # TODO: Get reverse IPs (need some information on netmask)
        # records = (record for records in self._records.values() for record in records)
        # ips = []
        # for record in records:
        #     if record.record_type != RecordType.A or record.record_type != RecordType.AAAA:
        #         continue

    @property
    def zones(self) -> Iterator[Tuple[int, Zone]]:
        for zone in self._zones.values():
            yield zone

    def zone_by_id(self, id: int) -> Tuple[int, Zone] | None:
        if id in self._zones:
            return self._zones[id]

        return None

    def zone(self, domain: DNSName) -> Tuple[int, Zone] | None:
        if domain in self._zones:
            return self._zones[domain]

        return None
