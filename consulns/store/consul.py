from base64 import b64encode
from consul import Consul as ConsulClient
from typing import Iterator, Literal, Tuple, TypedDict, Set, Union
from pydantic import UUID4, Field, TypeAdapter, BaseModel

from consulns.store.zone import Zone
from consulns.store.record import Record

from consulns.const import (
    CONSUL_PATH_CURRENT_ZONE,
    CONSUL_PATH_ZONES,
)


class ZoneAlreadyExists(Exception):
    pass


class ZoneDoesNotExist(Exception):
    pass


class KeyNotInserted(Exception):
    pass


class MissingChange(Exception):
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

    class ZoneNames(BaseModel):
        zones: Set[str]

    def _zone_names(self) -> ZoneNames:
        _, zones = self._kv_get(CONSUL_PATH_ZONES, self.ZoneNames)
        if zones is None:
            zones = self.ZoneNames(zones=set())
        return zones

    @property
    def zones(self) -> Iterator[Zone]:
        zone_names = self._zone_names()
        for zone_name in zone_names.zones:
            yield Zone(self, zone_name)

    def add_zone(self, zone: "Zone") -> None:
        zone_names = self._zone_names()
        if zone.name in zone_names.zones:
            raise ZoneAlreadyExists(zone.name)

        zone_names.zones.add(zone.name)
        z = self.ZoneNames(zones=zone_names.zones)
        self._kv_set(CONSUL_PATH_ZONES, z)

    def zone(self, zone_name: str) -> "Zone":
        for zone in self.zones:
            if zone.name == zone_name:
                return zone

        raise ZoneDoesNotExist(zone_name)

    class CurrentZone(BaseModel):
        zone: str

    def current_zone(self) -> "Zone | None":
        _, val = self._kv_get(CONSUL_PATH_CURRENT_ZONE, self.CurrentZone)
        if val is None:
            return None

        return self.zone(val.zone)

    def use_zone(self, zone: "Zone") -> None:
        cz = self.CurrentZone(zone=zone.name)
        self._kv_set(CONSUL_PATH_CURRENT_ZONE, cz)




class AddRecord(BaseModel):
    change_type: Literal["add"] = "add"
    record: Record

    @property
    def key(self) -> str:
        return f"add.{self.record.key}"


class DelRecord(BaseModel):
    change_type: Literal["del"] = "del"
    id: UUID4

    @property
    def key(self) -> str:
        id = b64encode(str(self.id).encode("utf-8")).decode("utf-8")
        return f"del.{id}"


class Change(BaseModel):
    update: Union[AddRecord, DelRecord] = Field(discriminator="change_type")

    @property
    def key(self) -> str:
        return self.update.key


