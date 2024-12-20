import click

from consulns.client.cli import cli
from consulns.client.consul import Record, RecordType, Zone
from consulns.client.zone import pass_zone

@cli.group()
def stage():
    pass

@stage.command()
@pass_zone
def status(zone: Zone):
    for i, change in enumerate(zone.changes):
        print(f"{i}\t{change.pretty_str}")

@stage.command()
@click.argument('record', type=str)
@click.argument('record_type', type=RecordType)
@click.argument('value', type=str)
@click.option('--ttl', type=int, default=300)
@pass_zone
def add(zone: Zone, record: str, record_type: RecordType, value: str, ttl: int):
    r = Record(
        record=record,
        record_type=record_type,
        value=value,
        ttl=ttl,
    )
    zone.add_record(r)
    print(f"Added record to zone {zone.name}")

stage.add_command(status)
stage.add_command(add)
