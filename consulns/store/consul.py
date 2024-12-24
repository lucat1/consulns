from consul import Consul as ConsulClient
from typing import Iterator, Tuple, TypedDict, Set
from dns.name import Name as DNSName, from_text as dns_from_text
from pydantic import TypeAdapter, BaseModel

from consulns.store.zone import Zone

from consulns.const import (
    CONSUL_PATH_CURRENT_ZONE,
    CONSUL_PATH_ZONES,
)


class ZoneAlreadyExists(Exception):
    pass


class MissingZone(Exception):
    pass


class KeyNotInserted(Exception):
    pass


class Consul:
    def __init__(self, client: ConsulClient) -> None:
        self._client = client

    class Value(TypedDict):
        LockIndex: int
        Key: str
        Flags: int
        Value: str
        CreateIndex: int
        ModifyIndex: int

    _value_ta = TypeAdapter(Value)

    def _kv_get[T: BaseModel](
        self, key: str, t: type[T]
    ) -> Tuple[int, T | None]:
        self._client.kv
        idx, raw_value = self._client.kv.get(key)
        if raw_value is None:
            return idx, None

        value = self._value_ta.validate_python(raw_value)
        result = t.model_validate_json(value["Value"])
        return idx, result

    def _kv_set(self, key: str, t: BaseModel) -> None:
        success = self._client.kv.put(key, t.model_dump_json())
        if not success:
            raise KeyNotInserted()

    class ZoneDNSNames(BaseModel):
        zones: Set[str]

    def _zone_names(self) -> ZoneDNSNames:
        _, zones = self._kv_get(CONSUL_PATH_ZONES, self.ZoneDNSNames)
        if zones is None:
            zones = self.ZoneDNSNames(zones=set())
        return zones

    @property
    def zones(self) -> Iterator[Zone]:
        zone_names = self._zone_names()
        for zone_name in zone_names.zones:
            yield Zone(self, dns_from_text(zone_name))

    def add_zone(self, zone: "Zone") -> None:
        assert zone.name[-1] != "."
        zone_names = self._zone_names()
        if zone.name in zone_names.zones:
            raise ZoneAlreadyExists(zone.name)

        zone_names.zones.add(str(zone.name))
        z = self.ZoneDNSNames(zones=zone_names.zones)
        self._kv_set(CONSUL_PATH_ZONES, z)

    def zone(self, zone_name: DNSName) -> "Zone":
        for zone in self.zones:
            if zone.name == zone_name:
                return zone

        raise MissingZone(zone_name)

    class CurrentZone(BaseModel):
        zone: str

    def current_zone(self) -> "Zone | None":
        _, val = self._kv_get(CONSUL_PATH_CURRENT_ZONE, self.CurrentZone)
        if val is None:
            return None

        return self.zone(dns_from_text(val.zone))

    def use_zone(self, zone: "Zone") -> None:
        cz = self.CurrentZone(zone=str(zone.name))
        self._kv_set(CONSUL_PATH_CURRENT_ZONE, cz)
