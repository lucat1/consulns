from enum import Enum
from pydantic import UUID4, IPvAnyAddress, BaseModel
from uuid import uuid4
from base64 import b64encode


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
        record = b64encode(self.record.encode("utf-8")).decode("utf-8")
        concatenated_value = f"{self.record_type.value}.{self.value}"
        value = b64encode(concatenated_value.encode("utf-8")).decode("utf-8")
        return f"{record}.{value}"

    @property
    def pretty_str(self) -> str:
        return (
            f"{self.record} IN {self.record_type.value} {self.ttl} {self.value}"
        )
