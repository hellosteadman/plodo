from ..digitalocean import DigitalOceanManager
from .utils import get_config, get_rack
from ..logs import get_remote_logs
import click
import os


@click.command()
@click.pass_context
@click.option('--tail', '-t', is_flag=True, help='Tail logs.')
@click.option('--rack', '-r', help='Rack to deploy to', default='production')
@click.argument('groups', nargs=-1, type=str)
def logs(ctx, groups, tail=False, rack='production'):
    """Read the logs of a server group"""
    options = get_config(ctx)
    rack_options = get_rack(ctx, options, rack)
    tag = rack_options.get('tag') or rack
    do_options = options.get('digitalocean', {})
    ssh_keys = options.get('ssh_keys')

    if isinstance(ssh_keys, list):
        ssh_keys = {}
        for key in options['ssh_keys']:
            ssh_keys[key] = os.getenv('SSH_KEY_%s' % key)
    elif not isinstance(ssh_keys, dict):
        ctx.fail('ssh_keys must be a dict')

    do_manager = DigitalOceanManager(**do_options)
    ips = []

    for group in groups:
        droplets = do_manager.get(
            'droplets',
            tag_name='%s-%s' % (tag, group)
        )

        for droplet in droplets['droplets']:
            ips.append(
                droplet['networks']['v4'][0]['ip_address']
            )

        if not any(ips):
            ctx.fail('No droplets found in %s group' % group)

    for key_id, key_filename in ssh_keys.items():
        get_remote_logs(key_filename, *ips, tail=tail)
        return
