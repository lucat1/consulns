import click
from tabulate import tabulate
from validators import domain as validate_domain

from consulns.client.cli import cli
from consulns.client.consul import pass_consul, pass_zone, Consul, Zone

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
        click.echo(f"{selected}{zone.name}\t{zone.serial}")

class InvalidDomain(Exception):
    pass

@zone.command()
@click.argument('zone_name', type=str)
@pass_consul
def add(consul: Consul, zone_name: str):
    if not validate_domain(zone_name):
        raise InvalidDomain(zone_name)
    consul.add_zone(Zone(consul, zone_name))
    click.secho(f"Zone added: {zone_name}", fg='green')

@zone.command()
@pass_zone
def show(zone: Zone):
    click.echo(f"Zone: {zone.name}")
    click.echo(f"Serial: {zone.serial}")

    records = []
    for record in zone.records:
        records.append((record.record, str(record.record_type), record.ttl, record.value, f"({record.id})"))
    if len(records) <= 0:
        click.echo("No records defined")
        return

    click.echo("Records:")
    tbl = tabulate(records, tablefmt='plain')
    tbl = "\n".join(f"  {s}" for s in tbl.split('\n'))
    click.echo(tbl)


@zone.command()
@click.argument('zone_name', type=str)
@pass_consul
def use(consul: Consul, zone_name: str):
    # Make sure the zone actually exists
    zone = consul.zone(zone_name)
    consul.use_zone(zone)
    click.secho(f"Selected zone: {zone.name}", fg='green')

zone.add_command(list)
zone.add_command(add)
zone.add_command(show)
zone.add_command(use)
