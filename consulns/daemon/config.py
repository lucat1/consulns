from pydantic import HttpUrl, UrlConstraints
from pydantic_settings import BaseSettings

from consulns.const import DEFAULT_CONSUL_PORT


class ConsulDsn(HttpUrl):
    """A type that will accept any Consul DSN.

    * Host required
    * Port not required (but defaulted)
    """

    _constraints = UrlConstraints(
        allowed_schemes=["http", "https"],
        host_required=True,
    )

    @property
    def host(self) -> str:
        """The required URL host."""
        return self._url.host  # pyright: ignore[reportReturnType]

    @property
    def port(self) -> int:
        """The required URL port."""
        return (
            self._url.port
            if self._url.port is not None
            else DEFAULT_CONSUL_PORT
        )


class Config(BaseSettings):
    consul_addr: ConsulDsn = ConsulDsn("http://127.0.0.1:8500")
