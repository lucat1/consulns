from rich.traceback import install

from consulns.client.cli import cli
from consulns.client.stage import stage
from consulns.client.zone import zone

# Install rich as a traceback handler
install(show_locals=True)

cli.add_command(zone)
cli.add_command(stage)

client = cli
