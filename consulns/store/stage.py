from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Literal, Union
from base64 import b64encode
from collections.abc import Iterator
from pydantic import UUID4, Field, BaseModel

from consulns.const import CONSUL_PATH_ZONE_STAGING
from consulns.store.record import Record

if TYPE_CHECKING:
    from consulns.store.zone import Zone


class MissingChange(Exception):
    pass


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


class Stage:
    def __init__(self, zone: Zone) -> None:
        self._zone = zone
        self.__staging = None

    class Staging(BaseModel):
        changes: Dict[str, Change] = {}

    @property
    def _staging(self) -> Staging:
        if self.__staging is None:
            staging_path = self._zone._compute_path(CONSUL_PATH_ZONE_STAGING)
            _, staging = self._zone._consul._kv_get(staging_path, self.Staging)
            if staging is None:
                staging = self.Staging()
            self.__staging = staging

        return self.__staging

    def _update_staging(self) -> None:
        staging_path = self._zone._compute_path(CONSUL_PATH_ZONE_STAGING)
        self._zone._consul._kv_set(staging_path, self._staging)

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

    def clear(self) -> None:
        self._staging.changes.clear()
        self._update_staging()
