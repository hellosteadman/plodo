from ..digitalocean import DigitalOceanManager
from .utils import get_config
import click
import os
import subprocess


@click.command()
@click.pass_context
def shell(ctx):
    """Access the Django shell of a worker server"""
    options = get_config(ctx)
    do_options = options.get('digitalocean', {})
    shell = options.get('shell', {})
    ssh_keys = options.get('ssh_keys')

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
        tag_name='plodo-%s' % shell_group
    )

    for droplet in droplets['droplets']:
        for key_id, key_filename in ssh_keys.items():
            parts = [
                'ssh',
                'root@%s' % droplet['networks']['v4'][0]['ip_address'],
                '-i', key_filename,
                shell_command
            ]

            proc = subprocess.Popen(parts)
            proc.wait()
            return
