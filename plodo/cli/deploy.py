from ..deployment import DropletDeployer
from .utils import get_config, get_rack
import click


@click.command()
@click.pass_context
@click.option('--debug', '-d', is_flag=True, help='Raise exceptions instead of squashing them.')
@click.option('--rack', '-r', help='Rack to deploy to', default='production')
@click.argument('groups', nargs=-1, type=str)
def deploy(ctx, groups, debug=False, rack='production'):
    """Deploy to rack"""
    options = get_config(ctx)
    rack_options = get_rack(ctx, options, rack)

    kwargs = dict(
        echo=click.echo,
        prompt=click.confirm,
        rack=rack
    )

    for key, value in options.items():
        if key in ('ssh_keys', 'region', 'ansible', 'digitalocean'):
            kwargs[key] = value

    for key, value in rack_options.items():
        if key in ('images', 'droplets', 'ansible', 'load_balancer'):
            kwargs[key] = value

    try:
        deployer = DropletDeployer(**kwargs)
    except TypeError as ex:
        if not debug:
            ctx.fail(ex)
        else:
            raise

    try:
        deployer.deploy(*groups)
    except Exception as ex:
        if not debug:
            ctx.fail(ex)
        else:
            raise
