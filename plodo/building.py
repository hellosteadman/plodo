from .droplets import DropletManagerBase
import os
import time


class ImageError(Exception):
    pass


class DropletBuilder(DropletManagerBase):
    def __init__(
        self, echo=None, prompt=None, region=None, ssh_keys={}, ansible={},
        images={}, **kwargs
    ):
        super().__init__(echo, prompt, region, ssh_keys, ansible, images)
        self._droplet_ids = {}

    def build(self, *groups):
        for group, kwargs in self.images.items():
            if not any(groups) or group in groups:
                images = self.build_image(group, **kwargs)

    def build_image(
        self, group, size='512mb', base=None, backups=False,
        user_data={}, monitoring=False, **kwargs
    ):
        base_image = self.find_base_image(group)
        first_droplet = None
        added_droplets = []

        for droplet in self._build(
            self.region,
            group,
            size,
            base,
            backups,
            user_data,
            monitoring
        ):
            droplet_id = droplet['id']

            if not group in self._droplet_ids:
                self._droplet_ids[group] = []

            self._droplet_ids[group].append(droplet_id)
            self.echo(
                'Created %s droplet %s from image %s.' % (
                    group,
                    droplet_id,
                    base_image or base
                )
            )

            if not self.provisioner.provision(group, droplet_id, '-deploy'):
                return

            if first_droplet is None:
                first_droplet = droplet

            added_droplets.append(droplet_id)

        for droplet_id in added_droplets:
            self.shutdown(droplet_id, delete=False)

        if base_image:
            self.do_manager.delete(
                'snapshots/%s' % base_image
            )

        if first_droplet:
            image_id = self.snapshot(group, first_droplet['id'])
            self.echo(
                '%s image ID: %s' % (group, image_id)
            )

    def destroy(self):
        for group, droplet_ids in self._droplet_ids.items():
            for droplet_id in droplet_ids:
                self.shutdown(droplet_id, delete=True)
