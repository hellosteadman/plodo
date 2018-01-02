from tempfile import mkstemp
from .digitalocean import DigitalOceanManager
import os
import subprocess
import sys
import time


class ProvisioningError(Exception):
    pass


class Provisioner:
    def __init__(
        self, echo=None, prompt=None, ssh_keys={}, ansible={}, digitalocean={}
    ):
        self.echo = echo or (lambda s: sys.stdout.write('%s\n' % s))
        self.prompt = prompt

        if isinstance(ssh_keys, dict):
            self.ssh_keys = ssh_keys
        elif isinstance(ssh_keys, list):
            self.ssh_keys = {}
            for key in ssh_keys:
                self.ssh_keys[key] = os.getenv('SSH_KEY_%s' % key)
        else:
            raise TypeError('ssh_keys must be a dict')

        if ansible is not None:
            if not isinstance(ansible, dict):
                raise TypeError('ansible must be a dict')
        else:
            raise TypeError('ansible is required')

        try:
            self.ansible_playbook = os.path.abspath(
                ansible['playbook']
            )

            self.ansible_homedir = ansible['home']
        except KeyError as ex:
            raise TypeError(
                'ansible.%s is required.' % (ex.args[0])
            )

        self.do_manager = DigitalOceanManager(**digitalocean)

    def _wait_multiple(self, droplet_ids):
        droplets = []
        for droplet_id in droplet_ids:
            droplets.append(
                self._wait(droplet_id)
            )

        self.echo('Waiting for droplet(s) to boot.')
        time.sleep(30)
        return droplets

    def _wait(self, droplet_id):
        while True:
            droplet = self.do_manager.get('droplets/%s' % droplet_id)
            droplet = droplet['droplet']

            if droplet['status'] == 'active':
                return droplet

            if droplet['status'] != 'new':
                raise Exception(
                    'Droplet %s entered invalid state "%s"' % (
                        droplet['id'],
                        droplet['state']
                    )
                )

            self.echo('Waiting for droplet(s) to come online.')
            time.sleep(15)

    def provision(self, group, droplet_ids, *tags):
        if not isinstance(droplet_ids, (list, tuple)):
            droplet_ids = [droplet_ids]

        droplets = self._wait_multiple(droplet_ids)
        return self._provision(group, droplets, *tags)

    def _provision(self, group, droplets, *tags):
        self.echo(
            'Provisioning %s droplet%s.' % (
                group,
                len(droplets) != 1 and 's' or ''
            )
        )

        handle, filename = mkstemp()
        cwd = os.getcwd()

        try:
            os.write(
                handle,
                ('[%s]\n' % group).encode('utf-8')
            )

            for droplet in droplets:
                os.write(
                    handle,
                    (
                        (
                            '%s '
                            'ansible_ssh_host=%s '
                            'ansible_ssh_user=root '
                            '%s '
                            'home=%s '
                            'ssl=True\n'
                        ) % (
                            droplet['name'],
                            droplet['networks']['v4'][0]['ip_address'],
                            ' '.join(
                                'ansible_ssh_private_key_file=%s' % f
                                for f in self.ssh_keys.values()
                            ),
                            self.ansible_homedir
                        )
                    ).encode('utf-8')
                )

            os.close(handle)
            os.environ.setdefault('ANSIBLE_HOST_KEY_CHECKING', 'False')

            args = [
                'ansible-playbook',
                '-i', filename,
                '--limit', group,
                os.path.join(cwd, self.ansible_playbook)
            ]

            include_tags = []
            exclude_tags = []

            for tag in tags:
                if tag.startswith('-'):
                    exclude_tags.append(tag[1:])
                else:
                    include_tags.append(tag)

            if any(include_tags):
                args.append('--tags')
                args.append(','.join(include_tags))

            if any(exclude_tags):
                args.append('--skip-tags')
                args.append(','.join(exclude_tags))

            while True:
                process = subprocess.Popen(tuple(args))
                if not process.wait():
                    return True

                if self.prompt is None:
                    raise ProvisioningError(
                        'Provisioning %s droplet%s failed.' % (
                            group,
                            len(droplets) != 1 and 's' or ''
                        )
                    )

                if not self.prompt(
                    'Provisioning %s droplet%s failed. Try again?' % (
                        group,
                        len(droplets) != 1 and 's' or ''
                    ),
                    default=True
                ):
                    return False
        finally:
            os.remove(filename)
