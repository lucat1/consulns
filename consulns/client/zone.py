import click
from rich import print

from consulns.client.cli import cli
from consulns.client.consul import pass_consul, Consul, Zone

@cli.group()
def zone():
    pass

@zone.command()
@pass_consul
def list(consul: Consul):
    for zone in consul.zones:
        print("zone", zone)

@zone.command()
@click.argument('zone_name', type=str)
@pass_consul
def add(consul: Consul, zone_name: str):
    consul.add_zone(Zone(consul, zone_name))
    print(f"Zone added: {zone_name}")

zone.add_command(list)
zone.add_command(add)
