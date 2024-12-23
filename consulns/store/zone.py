from __future__ import annotations

from base64 import b64encode
from enum import Enum
from consul import Consul as ConsulClient
from typing import TYPE_CHECKING, Iterator, Literal, Tuple, TypedDict, Set, Union, Dict
from uuid import uuid4
from pydantic import UUID4, Field, IPvAnyAddress, TypeAdapter, BaseModel

if TYPE_CHECKING:
    from consulns.store import Consul

from consulns.const import (
    CONSUL_PATH_ZONE_INFO,
    CONSUL_PATH_ZONE_RECORDS,
    CONSUL_PATH_ZONE_STAGING,
)

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
            if updt.change_type == "add":
                self._records.records[updt.record.id] = updt.record
            elif updt.change_type == "del":
                del self._records.records[updt.id]
            else:
                assert False
        # First, apply the changes to the records object.
        # If this fails, staging changes are preserved and the operation can be re-attempted.
        self._update_records()

        self._staging.changes.clear()
        self._update_staging()
