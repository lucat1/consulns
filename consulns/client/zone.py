import click
from functools import update_wrapper

from consulns.client.cli import cli
from consulns.client.consul import pass_consul, Consul, Zone
from consulns.const import CLICK_ZONE_CTX_KEY, ZONE_STORE_PATH

@cli.group()
def zone():
    pass

def current_zone() -> str | None:
    if ZONE_STORE_PATH.exists() and ZONE_STORE_PATH.is_file():
        return ZONE_STORE_PATH.read_text()
    else:
        return None

@zone.command()
@pass_consul
def list(consul: Consul):
    cz = current_zone()
    for zone in consul.zones:
        print("\t" if zone.name != cz else "*\t", zone.name, zone.serial)

@zone.command()
@click.argument('zone_name', type=str)
@pass_consul
def add(consul: Consul, zone_name: str):
    consul.add_zone(Zone(consul, zone_name))
    print(f"Zone added: {zone_name}")

@zone.command()
@click.argument('zone_name', type=str)
@pass_consul
def show(consul: Consul, zone_name: str):
    zone = consul.zone(zone_name)
    print(f"Zone: {zone.name}")
    print(f"Serial: {zone.serial}")

@zone.command()
@click.argument('zone_name', type=str)
@pass_consul
def use(consul: Consul, zone_name: str):
    # Make sure the zone actually exists
    zone = consul.zone(zone_name)
    ZONE_STORE_PATH.write_text(zone.name)
    print(f"Selected zone: {zone.name}")

zone.add_command(list)
zone.add_command(add)
zone.add_command(show)
zone.add_command(use)

class NoZoneSelected(Exception):
    pass

# The zone client is constructed lazyly as not all commands require it.
def pass_zone(f):
    @pass_consul
    @click.pass_context
    def new_func(ctx, consul: Consul, *args, **kwargs):
        if CLICK_ZONE_CTX_KEY not in ctx.obj:
            zone_name = current_zone()
            if zone_name is None:
                raise NoZoneSelected()

            ctx.obj[CLICK_ZONE_CTX_KEY] = consul.zone(zone_name)
            pass

        return ctx.invoke(f, ctx.obj[CLICK_ZONE_CTX_KEY ], *args, **kwargs)

    return update_wrapper(new_func, f)
