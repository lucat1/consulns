from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Iterator, Dict
from dns.name import Name as DNSName
from pydantic import UUID4, BaseModel

from consulns.store.record import Record
from consulns.store.stage import Stage

if TYPE_CHECKING:
    from consulns.store.consul import Consul

from consulns.const import (
    CONSUL_PATH_ZONE_INFO,
    CONSUL_PATH_ZONE_RECORDS,
)


class Zone:
    def __init__(self, consul: Consul, zone_name: DNSName) -> None:
        self._consul = consul
        self._zone_name = zone_name
        self.__info = None
        self.__stage = None
        self.__records = None

    @property
    def name(self) -> DNSName:
        return self._zone_name

    class ZoneInfo(BaseModel):
        serial: int = 0
        notified_serial: int = serial
        enabled: bool = True
        last_check: datetime = datetime.now()

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

    @property
    def enabled(self) -> bool:
        return self._info.enabled

    def set_enabled(self, enabled: bool) -> None:
        self._info.enabled = enabled
        return self._update_info()

    @property
    def last_check(self) -> datetime:
        return self._info.last_check

    def set_last_check(self, last_check: datetime) -> None:
        self._info.last_check = last_check
        return self._update_info()

    @property
    def notified_serial(self) -> int:
        return self._info.notified_serial

    def set_notified_serial(self, notified_serial: int) -> None:
        self._info.notified_serial = notified_serial
        return self._update_info()

    @property
    def stage(self) -> Stage:
        if self.__stage is None:
            self.__stage = Stage(self)

        return self.__stage

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
        for c in self.stage.changes:
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

        self.stage.clear()
