import click

from consulns.client.config import Config
from consulns.const import CLICK_CONFIG_CTX_KEY


@click.group()
@click.pass_context
def cli(ctx):
  ctx.ensure_object(dict)
  ctx.obj[CLICK_CONFIG_CTX_KEY] = Config()
