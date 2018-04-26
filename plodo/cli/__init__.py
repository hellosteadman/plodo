import click
from .build import build
from .deploy import deploy
from .provision import provision
from .scale import scale
from .shell import shell
from .logs import logs
from .ls import ls
from .ssh import ssh


@click.group(invoke_without_command=True)
@click.option('--rack', '-r', help='Rack to deploy to')
@click.pass_context
def main(ctx, rack='production'):
    """Django project deployment tool for DigitalOcean"""

    if ctx.invoked_subcommand is None:
        ctx.invoke(deploy)


main.add_command(build)
main.add_command(deploy)
main.add_command(provision)
main.add_command(scale)
main.add_command(shell)
main.add_command(logs)
main.add_command(ls)
main.add_command(ssh)
