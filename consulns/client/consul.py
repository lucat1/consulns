from base64 import b64encode
from enum import Enum
from typing import Iterator, Literal, Tuple, TypedDict, Set, Union, Dict
from uuid import uuid4
import click
from consul import Consul as ConsulClient
from functools import update_wrapper
from pydantic import UUID4, Field, IPvAnyAddress, TypeAdapter, BaseModel

from consulns.client.config import Config, pass_config
from consulns.const import CLICK_CONSUL_CTX_KEY, CONSUL_PATH_CURRENT_ZONE, CONSUL_PATH_ZONE_INFO, CONSUL_PATH_ZONE_RECORDS, CONSUL_PATH_ZONE_STAGING, CONSUL_PATH_ZONES, CLICK_ZONE_CTX_KEY

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
        self.client.kv
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

class RecordType(Enum):
    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    MX = "MX"

    CONSUL = "CONSUL"

    def __str__(self) -> str:
        return f"IN {self.value}"

class Record(BaseModel):
    id: UUID4 = uuid4()
    record: str
    record_type: RecordType
    value: IPvAnyAddress | str
    ttl: int

    @property
    def key(self) -> str:
        record = b64encode(self.record.encode('utf-8')).decode('utf-8')
        concatenated_value = f"{self.record_type.value}.{self.value}"
        value = b64encode(concatenated_value.encode('utf-8')).decode('utf-8')
        return f"{record}.{value}"

    @property
    def pretty_str(self) -> str:
        return f"{self.record} IN {self.record_type.value} {self.ttl} {self.value}"

class AddRecord(BaseModel):
    change_type: Literal['add'] = 'add'
    record: Record

    @property
    def key(self) -> str:
        return f"add.{self.record.key}"

class DelRecord(BaseModel):
    change_type: Literal['del'] = 'del'
    id: UUID4

    @property
    def key(self) -> str:
        id = b64encode(str(self.id).encode('utf-8')).decode('utf-8')
        return f"del.{id}"
    
class Change(BaseModel):
    update: Union[AddRecord, DelRecord] = Field(discriminator='change_type')

    @property
    def key(self) -> str:
        return self.update.key

class Zone:
    def __init__(self, consul: Consul, zone_name: str) -> None:
        self._consul = consul
        self._zone_name = zone_name
        self.__info = None
        self.__staging = None
        self.__records = None

    @property
    def name(self) -> str:
        return self._zone_name

    class ZoneInfo(BaseModel):
        serial: int = 0

    def _compute_path(self, path: str) -> str:
        return path.format(zone=self.name)

    @property
    def _info(self) -> ZoneInfo:
        if self.__info is None:
            info_path = self._compute_path(CONSUL_PATH_ZONE_INFO)
            _, info = self._consul._kv_get(info_path, self.ZoneInfo)
            if info is None:
                info = self.ZoneInfo()
            self.__info = info

        return self.__info

    def _update_info(self) -> None:
        info_path = self._compute_path(CONSUL_PATH_ZONE_INFO)
        self._consul._kv_set(info_path, self._info)
    
    @property
    def serial(self) -> int:
        return self._info.serial

    def set_serial(self, serial: int) -> None:
        self._info.serial = serial
        return self._update_info()

    class Staging(BaseModel):
        changes: Dict[str, Change] = {}

    @property
    def _staging(self) -> Staging:
        if self.__staging is None:
            staging_path = self._compute_path(CONSUL_PATH_ZONE_STAGING)
            _, staging = self._consul._kv_get(staging_path, self.Staging)
            if staging is None:
               staging = self.Staging()
            self.__staging = staging

        return self.__staging

    def _update_staging(self) -> None:
        staging_path = self._compute_path(CONSUL_PATH_ZONE_STAGING)
        self._consul._kv_set(staging_path, self._staging)

    @property
    def changes(self) -> Iterator[Change]:
        for value in self._staging.changes.values():
            yield value

    def add_record(self, record: Record) -> None:
        add_record = AddRecord(record=record)
        change = Change(update=add_record)
        self._staging.changes[change.key] = change
        self._update_staging()

    def del_record(self, record: Record) -> None:
        add_record = DelRecord(id=record.id)
        change = Change(update=add_record)
        self._staging.changes[change.key] = change
        self._update_staging()

    def revert(self, id: int) -> None:
        for i, change in enumerate(self.changes):
            if i == id:
                del self._staging.changes[change.key]
                self._update_staging()
                return

        raise MissingChange(id)

    class Records(BaseModel):
        records: Dict[UUID4, Record] = {}

    @property
    def _records(self) -> Records:
        if self.__records is None:
            records_path = self._compute_path(CONSUL_PATH_ZONE_RECORDS)
            _, records = self._consul._kv_get(records_path, self.Records)
            if records is None:
               records = self.Records()
            self.__records = records

        return self.__records

    def _update_records(self) -> None:
        records_path = self._compute_path(CONSUL_PATH_ZONE_RECORDS)
        self._consul._kv_set(records_path, self._records)

    @property
    def records(self) -> Iterator[Record]:
        for id, r in self._records.records.items():
            assert r.id == id
            yield r

    def record(self, id: UUID4) -> Record | None:
        if id in self._records.records:
            return self._records.records[id]

        return None

    def commit(self) -> None:
        for c in self.changes:
            updt = c.update
            if updt.change_type == 'add':
                self._records.records[updt.record.id] = updt.record
            elif updt.change_type == 'del':
                del self._records.records[updt.id]
            else:
                assert False
        # First, apply the changes to the records object.
        # If this fails, staging changes are preserved and the operation can be re-attempted.
        self._update_records()

        self._staging.changes.clear()
        self._update_staging()

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

class NoZoneSelected(Exception):
    pass

# The zone client is constructed lazyly as not all commands require it.
def pass_zone(f):
    @pass_consul
    @click.pass_context
    def new_func(ctx, consul: Consul, *args, **kwargs):
        if CLICK_ZONE_CTX_KEY not in ctx.obj:
            cz = consul.current_zone()
            if cz is None:
                raise NoZoneSelected()

            ctx.obj[CLICK_ZONE_CTX_KEY] = cz
            pass

        return ctx.invoke(f, ctx.obj[CLICK_ZONE_CTX_KEY ], *args, **kwargs)

    return update_wrapper(new_func, f)
