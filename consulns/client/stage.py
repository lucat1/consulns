import click
from pydantic import UUID4
from tabulate import tabulate

from consulns.client.cli import cli
from consulns.store import Record, RecordType, Zone
from consulns.client.ctx import pass_zone


@cli.group()
def stage():
    pass


@stage.command()
@pass_zone
def status(zone: Zone):
    cli_name = click.get_current_context().find_root().info_name
    click.echo(f"On zone {zone.name}")
    changes = []
    for change in zone.stage.changes:
        fg = "green" if change.update.change_type == "add" else "red"
        if change.update.change_type == "add":
            r = change.update.record
        else:
            r = zone.record(change.update.id)
            assert r is not None
        s = lambda s: click.style(s, fg=fg)

        changes.append(
            (s(r.record), s(str(r.record_type.value)), s(r.ttl), s(r.value))
        )
    if len(changes) <= 0:
        click.echo("No changes staged")
        return
    click.echo("Changes staged for commit:")
    click.echo(f"  (use {cli_name} revert <id> to revert a change)")
    click.echo(f"  (use {cli_name} commit to publish all changes)")

    tbl = tabulate(changes, tablefmt="plain")
    tbl = "\n".join(f"{i}\t{s}" for i, s in enumerate(tbl.split("\n")))
    click.echo(tbl)


@stage.command()
@click.argument("record", type=str)
@click.argument("record_type", type=RecordType)
@click.argument("value", type=str)
@click.option("--ttl", type=int, default=300)
@pass_zone
def add(zone: Zone, record: str, record_type: RecordType, value: str, ttl: int):
    r = Record(
        record=record,
        record_type=record_type,
        value=value,
        ttl=ttl,
    )
    zone.stage.add_record(r)
    click.echo(f"On zone {zone.name}")
    click.echo("Added record:")
    click.secho(
        f"\t{r.record} IN {r.record_type.value} {r.ttl} {r.value}", fg="green"
    )


class MissingRecord(Exception):
    pass


@stage.command(name="del")
@click.argument("id", type=UUID4)
@pass_zone
def delete(zone: Zone, id: UUID4):
    r = zone.record(id)
    if r is None:
        raise MissingRecord(id)

    zone.stage.del_record(r)
    click.echo(f"On zone {zone.name}")
    click.echo("Deleted record:")
    click.secho(
        f"\t{r.record} IN {r.record_type.value} {r.ttl} {r.value}", fg="red"
    )


@stage.command()
@click.argument("id", type=int)
@pass_zone
def revert(zone: Zone, id: int):
    zone.stage.revert(id)
    click.secho(f"Reverted staged change {id}", fg="yellow")


@stage.command()
@pass_zone
def commit(zone: Zone):
    l = len(list(zone.stage.changes))
    click.secho(
        f"Committing {l} change{'s' if l > 1 else ''} to zone {zone.name}...",
        fg="yellow",
    )
    zone.commit()
    click.secho(f"Updates applied successfully", fg="green")


stage.add_command(status)
stage.add_command(add)
stage.add_command(delete)
stage.add_command(revert)
stage.add_command(commit)
