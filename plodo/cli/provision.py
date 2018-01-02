from ..provisioning import Provisioner
from .utils import get_config
import click


@click.command()
@click.pass_context
@click.option('--debug', '-d', is_flag=True, help='Raise exceptions instead of squashing them.')
@click.argument('tag')
@click.argument('droplet_id')
def provision(ctx, tag, droplet_id, debug=False):
    """Provision a DigitalOcean droplet"""
    options = get_config(ctx)

    try:
        provisioner = Provisioner(
            echo=click.echo,
            prompt=click.confirm,
            ssh_keys=options.get('ssh_keys'),
            ansible=options.get('ansible')
        )
    except TypeError as ex:
        if not debug:
            ctx.fail(ex)
        else:
            raise

    try:
        provisioner.provision(tag, droplet_id)
    except Exception as ex:
        if not debug:
            ctx.fail(ex)
        else:
            raise
