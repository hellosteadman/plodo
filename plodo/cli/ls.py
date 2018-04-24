from ..digitalocean import DigitalOceanManager
from .utils import get_config, get_rack
from ..logs import get_remote_logs
import click
import os


@click.command()
@click.pass_context
@click.option('--rack', '-r', help='Rack to list', default='production')
@click.argument('groups', nargs=-1, type=str)
def ls(ctx, groups, tail=False, rack='production'):
    """Lists the servers currenty deploeyd to the selected rack"""
    options = get_config(ctx)
    rack_options = get_rack(ctx, options, rack)
    tag = rack_options.get('tag') or rack
    do_options = options.get('digitalocean', {})
    do_manager = DigitalOceanManager(**do_options)
    ips = []

    if not any(groups):
        groups = rack_options['droplets'].keys()

    for group in groups:
        click.echo()
        click.echo(group)
        click.echo('-' * 65)
        click.echo(
            'ID'.ljust(10) +
            'NAME'.ljust(40) +
            'IP ADDRESS'.ljust(16)
        )

        droplets = do_manager.get(
            'droplets',
            tag_name='%s-%s' % (tag, group)
        )

        for droplet in droplets['droplets']:
            click.echo(
                str(droplet['id']).ljust(10) +
                str(droplet['name']).ljust(40) +
                droplet['networks']['v4'][0]['ip_address'].ljust(16)
            )
