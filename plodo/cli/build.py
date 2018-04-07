from ..building import DropletBuilder
from .utils import get_config, get_rack
import click


@click.command()
@click.pass_context
@click.option('--debug', '-d', is_flag=True, help='Raise exceptions instead of squashing them.')
@click.option('--no-destroy', '-n', is_flag=True, help='Do not destroy droplets after creating them.')
@click.option('--rack', '-r', help='Rack to build for', default='production')
@click.argument('groups', nargs=-1, type=str)
def build(ctx, groups, debug=False, no_destroy=False, rack='production'):
    """Build images"""
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
        if key in ('ansible', 'images'):
            kwargs[key] = value

    try:
        builder = DropletBuilder(**kwargs)
    except TypeError as ex:
        if not debug:
            ctx.fail(ex)
        else:
            raise

    try:
        try:
            builder.build(*groups)
        except Exception as ex:
            if not debug:
                ctx.fail(ex)
            else:
                raise
    finally:
        if not no_destroy:
            builder.destroy()
