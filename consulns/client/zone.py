from rich import print

from consulns.client.cli import cli
from consulns.client.consul import pass_consul, Consul
from consulns.const import CONSUL_PATH_ZONES


@cli.command()
@pass_consul
def zones(consul: Consul):
  for zone in consul.zones:
    print('zone', zone)
