import click
from tabulate import tabulate

from consulns.client.cli import cli
from consulns.client.consul import Record, RecordType, Zone
from consulns.client.zone import pass_zone

@cli.group()
def stage():
    pass

@stage.command()
@pass_zone
def status(zone: Zone):
    cli_name = click.get_current_context().find_root().info_name
    click.echo(f"On zone {zone.name}")
    changes = []
    for change in zone.changes:
        fg = 'green' if change.update.change_type == 'add' else 'red'
        # TODO: display del changes!
        assert change.update.change_type == 'add'
        r = change.update.record
        s = lambda s: click.style(s, fg=fg)

        changes.append((s(r.record), s(f"IN {r.record_type.value}"), s(r.ttl), s(r.value)))
    if len(changes) <= 0:
        click.echo("No changes staged")
        return
    click.echo("Changes staged for commit:")
    click.echo(f"  (use {cli_name} revert <id> to revert a change)")
    click.echo(f"  (use {cli_name} commit to publish all changes)")

    tbl = tabulate(changes, tablefmt='plain')
    tbl = "\n".join(f"{i}\t{s}" for i, s in enumerate(tbl.split('\n')))
    click.echo(tbl)

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
    click.echo(f"On zone {zone.name}")
    click.echo("Added record:")
    click.secho(f"\t{r.record} IN {r.record_type.value} {r.ttl} {r.value}", fg='green')

@stage.command()
@click.argument('id', type=int)
@pass_zone
def revert(zone: Zone, id: int):
    zone.revert(id)
    click.secho(f"Reverted staged change {id}", fg='yellow')

@stage.command()
@pass_zone
def commit(zone: Zone):
    print(f"TODO: commit on zone {zone.name}")

stage.add_command(status)
stage.add_command(add)
stage.add_command(revert)
stage.add_command(commit)
