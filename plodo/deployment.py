from .droplets import DropletManagerBase
from .provisioning import Provisioner
import os


class DeploymenetError(Exception):
    pass


class DropletDeployer(DropletManagerBase):
    def __init__(
        self, echo=None, prompt=None, region=None, ssh_keys={}, ansible={},
        droplets={}, images={}, load_balancer={}, digitalocean={}, **kwargs
    ):
        super().__init__(
            echo,
            prompt,
            region,
            ssh_keys,
            ansible,
            images,
            digitalocean,
            rack=kwargs.get('rack', 'production')
        )

        if not isinstance(droplets, dict):
            raise TypeError('droplets must be a dict')

        if not isinstance(load_balancer, dict):
            raise TypeError('load_balancer must be a dict')

        for image, count in droplets.items():
            if not isinstance(count, int):
                raise TypeError(
                    'droplet "%s" must specify a count as an integer' % image
                )

        try:
            self.load_balancer_id = load_balancer['id']
        except KeyError:
            self.load_balancer_id = os.getenv(
                '%s_LOAD_BALANCER_ID' % kwargs.get(
                    'rack', 'production'
                ).upper()
            )

            if self.load_balancer_id is None:
                raise Exception(
                    'load_balancer.id is not defined'
                )

        try:
            self.load_balancer_group = load_balancer['group']
        except KeyError:
            raise Exception(
                'load_balancer.group is not defined'
            )

        self.droplets = droplets
        self._droplet_ids = {}

    def get_current_droplets(self, group):
        droplets = self.do_manager.get(
            'droplets',
            tag_name='%s-%s' % (self.tag_name, group)
        )

        return droplets['droplets']

    def deploy(self, *groups):
        for group, desired_count in self.droplets.items():
            if any(groups) and group not in groups:
                continue

            permanent = self.images.get(group, {}).get('permanent', False)
            old_droplets = self.get_current_droplets(group)
            front = self.images.get(group, {}).get('front', False)

            if not permanent:
                def destroy():
                    for droplet in old_droplets:
                        self.echo(
                            'Removing %s droplet %s.' % (
                                group,
                                droplet['id']
                            )
                        )

                        self.shutdown(droplet['id'], delete=True)

                if not front:
                    destroy()

            gap = desired_count - len(old_droplets)
            if gap > 0 or not permanent:
                droplets = self.scale_up(group, desired_count)
                if front and droplets and any(droplets):
                    destroy()

    def scale(self, group, count):
        current_droplets = self.get_current_droplets(group)
        gap = count - len(current_droplets)

        if gap > 1:
            return self.scale_up(group, gap)
        else:
            return self.scale_down(group, -gap)

    def scale_up(self, group, count):
        self.echo(
            'Adding %d %s droplet%s.' % (
                count,
                group,
                count != 1 and 's' or ''
            )
        )

        droplets = self._deploy(group, count)
        if droplets is None:
            return False

        if group == self.load_balancer_group and any(droplets):
            self.add_to_load_balancer(
                *[d['id'] for d in droplets]
            )

        return droplets

    def scale_down(self, group, count):
        self.echo(
            'Removing %d %s droplet%s.' % (
                count,
                group,
                count != 1 and 's' or ''
            )
        )

        droplets = self.get_current_droplets(group)

        for droplet in droplets[:count]:
            self.echo(
                'Removing %s droplet %s.' % (
                    group,
                    droplet['id']
                )
            )

            self.shutdown(droplet['id'], delete=True)

    def _deploy(self, group, count):
        added_droplets = []

        if not count:
            return

        image = self.find_base_image(group)
        if image is None:
            raise DeploymenetError(
                'No %s image found.' % group
            )

        yield_droplets = []
        for droplet in self._build(
            self.region,
            group,
            self.images[group].get('size', '512mb'),
            image,
            count=count
        ):
            droplet_id = droplet['id']

            if not group in self._droplet_ids:
                self._droplet_ids[group] = []

            self._droplet_ids[group].append(droplet_id)
            added_droplets.append(droplet_id)
            yield_droplets.append(droplet)

        def destroy():
            for droplet_id in added_droplets:
                self.echo(
                    'Destroying %s droplet %s.' % (
                        group,
                        droplet_id
                    )
                )

                self.do_manager.delete(
                    'droplets/%s' % droplet_id
                )

        try:
            if not self.provisioner.provision(
                group,
                added_droplets,
                'sync',
                'deploy'
            ):
                destroy()
                return
        except:
            destroy()
            raise
        else:
            return yield_droplets

    def add_to_load_balancer(self, *droplet_ids):
        self.echo(
            'Adding %d droplet%s to load balancer.' % (
                len(droplet_ids),
                len(droplet_ids) != 1 and 's' or ''
            )
        )

        return self.do_manager.post(
            'load_balancers/%s/droplets' % self.load_balancer_id,
            dict(
                droplet_ids=droplet_ids
            )
        )
