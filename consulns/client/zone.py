import click
from functools import update_wrapper
from validators import domain as validate_domain

from consulns.client.cli import cli
from consulns.client.consul import pass_consul, Consul, Zone
from consulns.const import CLICK_ZONE_CTX_KEY

@cli.group()
def zone():
    pass

@zone.command()
@pass_consul
def list(consul: Consul):
    cz = consul.current_zone()
    cz_name = None if cz is None else cz.name
    for zone in consul.zones:
        selected = "\t" if zone.name != cz_name else "*\t"
        print(f"{selected}{zone.name}\t{zone.serial}")

class InvalidDomain(Exception):
    pass

@zone.command()
@click.argument('zone_name', type=str)
@pass_consul
def add(consul: Consul, zone_name: str):
    if not validate_domain(zone_name):
        raise InvalidDomain(zone_name)
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
    consul.use_zone(zone)
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
            cz = consul.current_zone()
            if cz is None:
                raise NoZoneSelected()

            ctx.obj[CLICK_ZONE_CTX_KEY] = cz
            pass

        return ctx.invoke(f, ctx.obj[CLICK_ZONE_CTX_KEY ], *args, **kwargs)

    return update_wrapper(new_func, f)
