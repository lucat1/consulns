from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Annotated, List as TList, Literal, Optional, Dict
from pydantic import BaseModel, Field, TypeAdapter

from consulns.store.zone import AddKey, Key


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


class GetDomainInfoParameters(BaseModel):
    name: str


class GetDomainInfo(BaseModel):
    method: Literal["getDomainInfo"]
    parameters: GetDomainInfoParameters


class QType(Enum):
    ANY = "ANY"
    SOA = "SOA"

    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    MX = "MX"
    NS = "NS"


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


class GetAllDomainMetadataParameters(BaseModel):
    name: str


class GetAllDomainMetadata(BaseModel):
    method: Literal["getAllDomainMetadata"]
    parameters: GetAllDomainMetadataParameters


class GetDomainMetadataParameters(BaseModel):
    name: str
    kind: str


class GetDomainMetadata(BaseModel):
    method: Literal["getDomainMetadata"]
    parameters: GetDomainMetadataParameters


class SetDomainMetadataParameters(BaseModel):
    name: str
    kind: str
    value: TList[str]


class SetDomainMetadata(BaseModel):
    method: Literal["setDomainMetadata"]
    parameters: SetDomainMetadataParameters


class GetDomainKeysParameters(BaseModel):
    name: str


class GetDomainKeys(BaseModel):
    method: Literal["getDomainKeys"]
    parameters: GetDomainKeysParameters


class AddDomainKeyParameters(BaseModel):
    name: str
    key: AddKey


class AddDomainKey(BaseModel):
    method: Literal["addDomainKey"]
    parameters: AddDomainKeyParameters


class RemoveDomainKeyParameters(BaseModel):
    name: str
    id: int


class RemoveDomainKey(BaseModel):
    method: Literal["removeDomainKey"]
    parameters: RemoveDomainKeyParameters


class GetBeforeAndAfterNamesAbsoluteParameters(BaseModel):
    qname: str


class GetBeforeAndAfterNamesAbsolute(BaseModel):
    method: Literal["getBeforeAndAfterNamesAbsolute"]
    parameters: GetBeforeAndAfterNamesAbsoluteParameters


class StartTransactionParameters(BaseModel):
    domain: str
    domain_id: int
    trxid: int


class StartTransaction(BaseModel):
    method: Literal["startTransaction"]
    parameters: StartTransactionParameters


class CommitTransactionParameters(BaseModel):
    trxid: int


class CommitTransaction(BaseModel):
    method: Literal["commitTransaction"]
    parameters: CommitTransactionParameters


# From: https://stackoverflow.com/a/78984348
Query = (
    Initialize
    | GetAllDomains
    | GetDomainInfo
    | Lookup
    | List
    | GetAllDomainMetadata
    | GetDomainMetadata
    | SetDomainMetadata
    | GetDomainKeys
    | AddDomainKey
    | RemoveDomainKey
    | GetBeforeAndAfterNamesAbsolute
    | StartTransaction
    | CommitTransaction
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


class BeforeAndAfterNames(BaseModel):
    before: str
    after: str
    unhashed: str


class Response(BaseModel):
    result: (
        bool
        | TList[DomainInfo]
        | DomainInfo
        | TList[RecordInfo]
        | TList[Key]
        | Dict[str, TList[str]]
        | TList[str]
        | BeforeAndAfterNames
    )
