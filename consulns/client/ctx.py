import click
from consul import Consul as ConsulClient
from functools import update_wrapper

from consulns.store import Consul
from consulns.client.config import Config, pass_config
from consulns.const import CLICK_CONSUL_CTX_KEY, CLICK_ZONE_CTX_KEY

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

class NoZoneSelected(Exception):
    pass

# The zone client is constructed lazyly as not all commands require it.
def pass_zone(f):
    @pass_consul
    @click.pass_context
    def new_func(ctx, consul: Consul, *args, **kwargs):
        if CLICK_ZONE_CTX_KEY not in ctx.obj:
            cz = consul.current_zone()
            if cz is None:
                raise NoZoneSelected()

            ctx.obj[CLICK_ZONE_CTX_KEY] = cz
            pass

        return ctx.invoke(f, ctx.obj[CLICK_ZONE_CTX_KEY ], *args, **kwargs)

    return update_wrapper(new_func, f)
