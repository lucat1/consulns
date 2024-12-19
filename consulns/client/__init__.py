from rich.traceback import install

from consulns.client.cli import cli
from consulns.client.zone import zones

# Install rich as a traceback handler
install(show_locals=True)

cli.add_command(zones)

client = cli
