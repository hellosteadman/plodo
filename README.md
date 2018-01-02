# Plodo

Plodo is a tool I built to build and deploy [Podiant](https://podiant.co/)'s web and worker servers, in an immutable fashion, with new servers being spun up to replace old ones, instead of constantly updating existing servers (or "cattle" vs "pets").

The process for creating images and deploying droplets isn't quick, because DigitalOcean still takes a bit of time to create droplets from images, but it works for me.

**This tool is designed to run with Python 3, and is not tested against Python 2.**

## Installation

Simply run:

    $ pip install plodo

or

    $ pip3 install plodo

The tool is designed to be run directly from the terminal, so doesn't need to be in a virtualenv.

## Configuration

When installed, Plodo will look for a configuration file (called _plodo.conf_) in the current working directory. A smaple configuration file looks like this:

```yaml
---

digitalocean:
    api_version: 2
    api_token: abcdefghijklmnopqrstuvwxyz1234567890 # Your DigitalOcean API token

region: lon1 # The DigitalOcean region to create droplets and snapshots
ssh_keys:
    12345678: /path/to/keyfile # The ID of an SSH key stored within DigitalOcean, and the local path to the key file

ansible:
    playbook: ./ansible/production.yaml # The Ansible playbook to run
    home: /var/app/ # The remote home directory for the app

images: # A collection of arbitrary group names with configuration options
    cron:
        size: 512mb # The droplet size
        base: ubuntu-16-04-x64 # The base image to use if running `plodo build` for the first time
        monitoring: true # Enable monitoring for the droplet
    worker:
        size: 2gb
        base: ubuntu-16-04-x64
        monitoring: true
    web:
        size: 2gb
        base: ubuntu-16-04-x64
        monitoring: true
        front: true # Denotes a public-facing droplet, which changes the order of how droplets are destroyed and created

droplets: # The target number of droplets to deploy in each group
    cron: 1
    worker: 2
    web: 5

load_balancer:
    id: 725498b1-6553-4e88-9d14-e8812f9f591d # The ID of a DigitalOcean load balancer to add droplets to
    group: web # The group whose droplets should be added to the load balancer

shell:
    group: worker # The droplet group used to find servers that can run a shell command
    user: root # The Unix user to SSH in as
    command: podiant shell # The command to run on the droplet to access a shell
```

### Storing the configuration file

You should store the file in the root directory of your app, and run `plodo` from there.

If you want to add the file to your repo, you can change the configuration accordingly:

```yaml
# Remove the `digitalocean.api_key` setting, or the entire `digitalocean` object.
digitalocean:
    api_version: 2

# Change `ssh_keys` from an object to a list of DigitalOcean SSH key IDs
ssh_keys:
    - 12345678
```

Once done, you can set the following environment variables:

```sh
SSH_KEY_12345678=/path/to/sshkey # Change '12345678' to the ID of your SSH key within DigitalOcean
DO_API_VERSION=2 # Optional
DO_API_TOKEN=abcdefghijklmnopqrstuvwxyz1234567890 # Your DigitalOcean API token
```

## Usage

To use it:

```
$ plodo --help
```

## Commands

You can add the `--help` option to any command to display a list of options and arguments for that command.

To diagnose issues, use the `-d` or `--debug` option. This will show a complete stack trace of errors, when raised.

### `plodo build`

This command creates either completely fresh snapshots - based off an Ubuntu image - or layer changes ontop of an existing snapshot. A droplet is spun up, an Ansible playbook is run, then the state of the droplet is saved as a snapshot.

The next time `plodo build` is run, it sues _that_ snapshot to create a new one, then removes the old one.

Once the snapshots are saved, the droplets used to create them are destroyed.

#### Arguments

Optionally specify a list of droplet groups (such as `web` or `worker`) that should be built. This is useful if you only need to rebuild a worker server's snapshot, for example.

#### Options

  - `-n`, `--no-destroy`: Do not destroy droplets after using them to create snapshots.

### `plodo deploy`

This command spins up new droplets using the snapshots created in `plodo build`. It runs an Ansible playbook to deliver updated files, start necessary services, and add web droplets to a load balancer.

Once the new droplets are in place, old droplets are removed (this is done in a different order depending on whether the servers are public-facing or not).

#### Arguments

Optionally specify a list of droplet groups (such as `web` or `worker`) that should be deployed. This is only really useful in situations where you quickly need to upload new code to a specific server group, as the end goal is to have all server groups running the same code.

### `plodo provision <tag> <droplet_id>`

This command runs the Ansible playbook against a given DigitalOcean droplet. It's really a shortcut for quickly deploying code changes to a specific droplet, and was written to test and diagnose provisioning of droplets via Ansible.

#### Arguments

The first argument must be an Ansible tag. This tag is added to the `ansible-playbook` command.

The second argument is the ID to a DigitalOcean droplet.

### `plodo scale`

This command is used to scale a group of servers up or down. Plodo will then ensure the specified number of droplets are running, and either remove droplets no longer needed, or add new ones.

#### Arguments

Specify the group name and a number in key-pair fashion, like so:

### `plodo shell`

This command uses SSH to run an arbitrary command on the first server in a group, specified in the config.

Because the tool was initially designed to deploy a Django app, my config uses an equivalent of `manage.py shell` to access the Django shell, so I can interact with models with one command, without ever needing to know the IP address of a server.

## Known issues

- `plodo scale` has an issue where it incorrectly calculates the number of droplets it needs to create, when scaling to 1.

## Support

I can't guarantee that I'll be able to provide support, but if you notice a bug or you have an improvement, I'll gladly accept a pull request.

## Why no tests?

The tool was built quickly with a singular purpose, and was tested IRL. I am a fan of TDD but it wasn't an appropriate methodology for the work I needed to do here.

If you'd like to write tests, perhaps by faking responses from the DigitalOcean API, I'll be more than happy to accept a pull request.
