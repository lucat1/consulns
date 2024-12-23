from rich.traceback import install

from consulns.client.cli import cli
from consulns.client.stage import stage, status, add, delete, revert, commit
from consulns.client.zone import show, zone

# Install rich as a traceback handler
install(show_locals=True)

cli.add_command(zone)
# re-exposing stage commands
cli.add_command(show)

cli.add_command(stage)
# re-exposing stage commands
cli.add_command(status)
cli.add_command(add)
cli.add_command(delete)
cli.add_command(revert)
cli.add_command(commit)

client = cli
