from rich.traceback import install

from consulns.client.cli import cli
from consulns.client.stage import stage, status, add
from consulns.client.zone import zone

# Install rich as a traceback handler
install(show_locals=True)

cli.add_command(zone)
cli.add_command(stage)

# re-exposing stage commands
cli.add_command(status)
cli.add_command(add)

client = cli
