import click
from rich import print

from consulns.client.cli import cli
from consulns.client.consul import Record, RecordType, RecordValue, Zone
from consulns.client.zone import pass_zone

@cli.group()
def stage():
    pass

@stage.command()
@pass_zone
def list(zone: Zone):
    # TODO
    print("listing domains")

@stage.command()
@click.argument('stage', type=str)
@click.argument('record_type', type=RecordType)
@click.argument('value', type=str)
@click.option('--ttl', type=int, default=300)
@pass_zone
def add(zone: Zone, record: str, record_type: RecordType, value: str, ttl: int):
    r = Record(
        record=record,
        value=RecordValue(
            record_type=record_type,
            value=value
        ),
        ttl=ttl,
    )
    zone.add_record(r)
    for change in zone.changes:
        print('change', change)
    print(zone.name)

stage.add_command(list)
stage.add_command(add)
