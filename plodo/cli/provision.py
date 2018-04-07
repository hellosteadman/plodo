from ..provisioning import Provisioner
from .utils import get_config, get_rack
import click


@click.command()
@click.pass_context
@click.option('--debug', '-d', is_flag=True, help='Raise exceptions instead of squashing them.')
@click.option('--rack', '-r', help='Rack to provision', default='production')
@click.argument('tag')
@click.argument('droplet_id')
def provision(ctx, tag, droplet_id, debug=False, rack='production'):
    """Provision a DigitalOcean droplet"""
    options = get_config(ctx)
    rack_options = get_rack(ctx, options, rack)

    kwargs = dict(
        echo=click.echo,
        prompt=click.confirm
    )

    for key, value in options.items():
        if key in ('ssh_keys', 'ansible', 'digitalocean'):
            kwargs[key] = value

    if 'ansible' in rack_options:
        kwargs['ansible'] = rack_options['ansible']

    try:
        provisioner = Provisioner(**kwargs)
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
