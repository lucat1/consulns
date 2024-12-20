from typing import Iterator, Tuple, TypedDict, Set, Self
import click
from consul import Consul as ConsulClient
from functools import update_wrapper
from pydantic import TypeAdapter, BaseModel

from consulns.client.config import Config, pass_config
from consulns.const import CLICK_CONSUL_CTX_KEY, CONSUL_PATH_ZONES

class ZoneAlreadyExists(Exception):
    pass

class KeyNotInserted(Exception):
    pass

class Consul:
    def __init__(self, client: ConsulClient) -> None:
        self.client = client

    class Value(TypedDict):
        LockIndex: int
        Key: str
        Flags: int
        Value: str
        CreateIndex: int
        ModifyIndex: int

    _value_ta = TypeAdapter(Value)

    def _kv_get[T: BaseModel](self, key: str, t: type[T]) -> Tuple[int, T | None]:
        idx, raw_value = self.client.kv.get(key)
        if raw_value is None:
            return idx, None

        value = self._value_ta.validate_python(raw_value)
        result = t.model_validate_json(value["Value"])
        return idx, result

    def _kv_set(self, key: str, t: BaseModel) -> None:
        success = self.client.kv.put(key, t.model_dump_json())
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
    def zones(self) -> Iterator["Zone"]:
        zone_names = self._zone_names()
        for zone_name in zone_names.zones:
            yield Zone(self, zone_name)

    def add_zone(self, zone: "Zone") -> None:
        zone_names = self._zone_names()
        if zone.name in zone_names.zones:
            raise ZoneAlreadyExists()

        zone_names.zones.add(zone.name)
        z = self.ZoneNames(zones=zone_names.zones)
        self._kv_set(CONSUL_PATH_ZONES, z)

class Zone:
    def __init__(self, consul: Consul, zone_name: str) -> None:
        self._consul = consul
        self._zone_name = zone_name

    @property
    def name(self) -> str:
        return self._zone_name

    # def __eq__(self, other: Self) -> bool:
    #     return self.zone_name == other.zone_name

# The consul client is constructed lazyly as not all commands require it.
def pass_consul(f):
    @pass_config
    @click.pass_context
    def new_func(ctx, config: Config, *args, **kwargs):
        if CLICK_CONSUL_CTX_KEY not in ctx.obj:
            scheme = config.consul_addr.scheme
            host = config.consul_addr.host
            port = config.consul_addr.port
            ctx.obj[CLICK_CONSUL_CTX_KEY] = Consul(
                ConsulClient(scheme=scheme, host=host, port=port)
            )
            pass

        return ctx.invoke(f, ctx.obj[CLICK_CONSUL_CTX_KEY], *args, **kwargs)

    return update_wrapper(new_func, f)
