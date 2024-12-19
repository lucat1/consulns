from typing import Iterator
import click
from consul import Consul as ConsulClient
from functools import update_wrapper

from consulns.client.config import Config, pass_config
from consulns.const import CLICK_CONSUL_CTX_KEY, CONSUL_PATH_ZONES


class Zone:
  pass


class Consul:
  def __init__(self, client: ConsulClient) -> None:
    self.client = client

  @property
  def zones(self) -> Iterator[Zone]:
    # TODO
    kv = self.client.kv.get(CONSUL_PATH_ZONES)
    yield Zone()


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
