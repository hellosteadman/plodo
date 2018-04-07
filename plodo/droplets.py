from datetime import datetime
from operator import itemgetter
from .digitalocean import DigitalOceanManager
from .provisioning import Provisioner, ProvisioningError
import re
import time
import sys


IMAGE_NAME_REGEX = re.compile(
    r'^([\w-]+)-([\w-]+)-(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})$'
)


class DropletError(Exception):
    pass


class DropletManagerBase:
    def __init__(
        self, echo=None, prompt=None, region=None,
        ssh_keys={}, ansible={}, images={}, digitalocean={}, rack='production'
    ):
        self.echo = echo or (lambda s: sys.stdout.write('%s\n' % s))
        self.prompt = prompt
        self.tag_name = rack

        if not region or not isinstance(region, str):
            raise TypeError('region must be a string')

        self.region = region
        self.provisioner = Provisioner(
            echo, prompt, ssh_keys, ansible, digitalocean
        )

        self.ssh_keys = self.provisioner.ssh_keys
        self.do_manager = DigitalOceanManager(**digitalocean)

        if not isinstance(images, dict):
            raise TypeError('images must be a dict')

        for key, image in images.items():
            if not isinstance(image, dict):
                raise TypeError(
                    'image "%s" must be a dict' % (key)
                )

        self.images = images

    def find_base_image(self, tag):
        images = self.do_manager.get('snapshots')
        image_dates = []

        for image in images.get('snapshots', []):
            match = IMAGE_NAME_REGEX.match(image['name'])
            if match is not None:
                (
                    match_rack,
                    match_tag,
                    match_year,
                    match_month,
                    match_day,
                    match_hour,
                    match_minute,
                    match_second
                ) = match.groups()

                if match_rack != self.tag_name:
                    continue

                if match_tag != tag:
                    continue

                date = datetime(
                    int(match_year),
                    int(match_month),
                    int(match_day),
                    int(match_hour),
                    int(match_minute),
                    int(match_second)
                )

                image_dates.append(
                    (date, image['id'])
                )

        if any(image_dates):
            image_dates = sorted(image_dates, key=itemgetter(0))
            return image_dates[-1][1]

        return None

    def _build(
        self, region, tag, size='512mb', base=None, backups=False,
        user_data={}, monitoring=False, count=1
    ):
        def unique_id():
            return hex(int(time.time() * 10000000))[2:]

        if not base:
            raise TypeError('Bsae image is required.')

        droplet_name = '%s-%s' % (tag, unique_id())
        droplets = self.do_manager.post(
            'droplets',
            dict(
                names=[
                    '%s-%d' % (droplet_name, i + 1)
                    for i in range(0, count)
                ],
                region=region,
                size=size,
                image=base,
                ssh_keys=list(self.ssh_keys.keys()),
                backups=not not backups,
                user_data=user_data or None,
                monitoring=not not monitoring,
                tags=['%s-%s' % (self.tag_name, tag)]
            )
        )

        for droplet in droplets['droplets']:
            yield droplet

    def snapshot(self, tag, droplet_id):
        action = self.do_manager.post(
            'droplets/%s/actions' % droplet_id,
            dict(
                type='snapshot',
                name='%s-%s-%s' % (
                    self.tag_name,
                    tag,
                    datetime.now().strftime('%Y%m%d%H%I%S')
                )
            )
        )

        return action['action']['resource_id']

    def shutdown(self, droplet_id, delete=False):
        droplet = self.do_manager.get('droplets/%s' % droplet_id)
        if droplet['droplet']['status'] in ('off', 'archive'):
            if delete:
                self.echo('Destroying droplet %s.' % droplet_id)
                self.do_manager.delete('droplets/%s' % droplet_id)

            return

        action = self.do_manager.post(
            'droplets/%s/actions' % droplet_id,
            dict(type='shutdown')
        )

        action_id = action['action']['id']

        while True:
            self.echo('Waiting for droplet %s to shut down.' % droplet_id)
            time.sleep(15)

            action = self.do_manager.get(
                'droplets/%s/actions/%s' % (
                    droplet_id,
                    action_id
                )
            )

            if action['action']['status'] == 'completed':
                if delete:
                    self.echo('Destroying droplet %s.' % droplet_id)
                    self.do_manager.delete('droplets/%s' % droplet_id)

                return True

            if action['action']['status'] == 'errored':
                raise DropletError(
                    'An unknown error occurred while issuing the shutdown command.'
                )
