from ..deployment import DropletDeployer
from .utils import get_config
import click


@click.command()
@click.pass_context
@click.option('--debug', '-d', is_flag=True, help='Raise exceptions instead of squashing them.')
@click.argument('groups', nargs=-1, type=str)
def deploy(ctx, groups, debug=False):
    """Deploy to production environment"""
    options = get_config(ctx)

    try:
        deployer = DropletDeployer(
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
        deployer.deploy(*groups)
    except Exception as ex:
        if not debug:
            ctx.fail(ex)
        else:
            raise
