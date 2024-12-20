from pydantic import HttpUrl, UrlConstraints
from pydantic_settings import BaseSettings
from functools import update_wrapper
import click

from consulns.const import CLICK_CONFIG_CTX_KEY, DEFAULT_CONSUL_PORT


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


def pass_config(f):
    @click.pass_context
    def new_func(ctx, *args, **kwargs):
        return ctx.invoke(f, ctx.obj[CLICK_CONFIG_CTX_KEY], *args, **kwargs)

    return update_wrapper(new_func, f)
