import click
from .build import build
from .deploy import deploy
from .provision import provision
from .scale import scale
from .shell import shell
from .logs import logs


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    """Django project deployment tool for DigitalOcean"""

    if ctx.invoked_subcommand is None:
        ctx.invoke(deploy)


main.add_command(build)
main.add_command(deploy)
main.add_command(provision)
main.add_command(scale)
main.add_command(shell)
main.add_command(logs)
