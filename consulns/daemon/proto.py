from pathlib import Path
from typing import Annotated, Literal
from pydantic import BaseModel, Field, TypeAdapter


class InitializeParameters(BaseModel):
    path: Path

class Initialize(BaseModel):
    method: Literal['initialize']
    parameters: InitializeParameters

# From: https://stackoverflow.com/a/78984348
Message = Initialize
MessageAdapter: TypeAdapter[Message] = TypeAdapter(
    Annotated[Message, Field(discriminator="method")]
)
