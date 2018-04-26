from ..digitalocean import DigitalOceanManager
from .utils import get_config, get_rack
from requests.exceptions import HTTPError
import click
import os
import subprocess


@click.command()
@click.option('--rack', '-r', help='Rack to execute on', default='production')
@click.pass_context
@click.argument('id', type=str)
def ssh(ctx, id, rack='production'):
    """SSH into a droplet"""
    options = get_config(ctx)
    do_options = options.get('digitalocean', {})
    shell = options.get('shell', {})
    ssh_keys = options.get('ssh_keys')
    rack_options = get_rack(ctx, options, rack)
    tag = rack_options.get('tag') or rack

    if isinstance(ssh_keys, list):
        ssh_keys = {}
        for key in options['ssh_keys']:
            ssh_keys[key] = os.getenv('SSH_KEY_%s' % key)
    elif not isinstance(ssh_keys, dict):
        ctx.fail('ssh_keys must be a dict')

    shell_user = shell.get('user', 'root')

    do_manager = DigitalOceanManager(**do_options)

    try:
        droplet = do_manager.get(
            'droplets/%s' % id
        )
    except HTTPError as ex:
        if ex.response.status_code == 404:
            ctx.fail('No droplet found with ID %s' % id)
            return

    click.echo('Running bash on droplet %(id)s' % droplet['droplet'])
    click.echo()

    for key_id, key_filename in ssh_keys.items():
        do_manager.ssh(droplet['droplet'], key_filename)
        return
