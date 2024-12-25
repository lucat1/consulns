from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated, List as TList, Literal, Optional, Union
from pydantic import BaseModel, Field, IPvAnyAddress, TypeAdapter


class InitializeParameters(BaseModel):
    path: Path


class Initialize(BaseModel):
    method: Literal["initialize"]
    parameters: InitializeParameters


class GetAllDomainsParameters(BaseModel):
    include_disabled: bool


class GetAllDomains(BaseModel):
    method: Literal["getAllDomains"]
    parameters: GetAllDomainsParameters


class GetAllDomainMetadataParameters(BaseModel):
    name: str


class GetAllDomainMetadata(BaseModel):
    method: Literal["getAllDomainMetadata"]
    parameters: GetAllDomainMetadataParameters


class QType(Enum):
    ANY = "ANY"
    SOA = "SOA"

    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    MX = "MX"


class LookupParameters(BaseModel):
    qname: str
    qtype: QType
    zone_id: Optional[int] = Field(alias="zone-id")


class Lookup(BaseModel):
    method: Literal["lookup"]
    parameters: LookupParameters


class ListParameters(BaseModel):
    zonename: str
    domain_id: int


class List(BaseModel):
    method: Literal["list"]
    parameters: ListParameters


class GetDomainKeysParameters(BaseModel):
    name: str


class GetDomainKeys(BaseModel):
    method: Literal["getDomainKeys"]
    parameters: GetDomainKeysParameters


# From: https://stackoverflow.com/a/78984348
Query = (
    Initialize
    | GetAllDomains
    | Lookup
    | GetAllDomainMetadata
    | List
    | GetDomainKeys
)
QueryAdapter: TypeAdapter[Query] = TypeAdapter(
    Annotated[Query, Field(discriminator="method")]
)


class ZoneKind(Enum):
    NATIVE = "native"
    MASTER = "master"
    SLAVE = "slave"


class DomainInfo(BaseModel):
    id: int
    zone: str
    serial: int
    notified_serial: int
    last_check: datetime
    kind: ZoneKind


class RecordInfo(BaseModel):
    qtype: QType
    qname: str
    content: str
    ttl: int
    auth: bool


class Response(BaseModel):
    result: Union[bool, TList[DomainInfo], TList[RecordInfo]]
