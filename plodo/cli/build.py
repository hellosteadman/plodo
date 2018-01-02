from ..building import DropletBuilder
from .utils import get_config
import click


@click.command()
@click.pass_context
@click.option('--debug', '-d', is_flag=True, help='Raise exceptions instead of squashing them.')
@click.option('--no-destroy', '-n', is_flag=True, help='Do not destroy droplets after creating them.')
@click.argument('groups', nargs=-1, type=str)
# @click.argument('name', default='world', required=False)
def build(ctx, groups, debug=False, no_destroy=False):
    """Build images"""
    options = get_config(ctx)

    try:
        builder = DropletBuilder(
            echo=click.echo,
            prompt=click.confirm,
            **options
        )
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
