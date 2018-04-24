from ..digitalocean import DigitalOceanManager
from .utils import get_config, get_rack
import click
import os
import subprocess


@click.command()
@click.option('--rack', '-r', help='Rack to execute on', default='production')
@click.pass_context
def shell(ctx, rack='production'):
    """Access the Django shell of a worker server"""
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

    if not shell.get('group'):
        ctx.fail('shell.group not defined.')

    if not shell.get('command'):
        ctx.fail('shell.command not defined.')

    shell_group = shell['group']
    shell_user = shell.get('user', 'root')
    shell_command = shell['command']

    do_manager = DigitalOceanManager(**do_options)
    droplets = do_manager.get(
        'droplets',
        tag_name='%s-%s' % (tag, shell_group)
    )

    for droplet in droplets['droplets']:
        for key_id, key_filename in ssh_keys.items():
            do_manager.run(droplet, key_filename, shell_command)
            return

    ctx.fail('No droplet found in shell group')
