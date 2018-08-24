import os
import requests
import subprocess


class DigitalOceanManager:
    def __init__(self, api_version=None, api_token=None):
        self.api_version = api_version or os.getenv('DO_API_VERSION', '2')
        self.api_token = api_token or os.getenv('DO_API_TOKEN')

        if not self.api_token:
            raise TypeError('Missing DigitalOcean API token.')

        self.base_url = 'https://api.digitalocean.com/v%s/' % self.api_version

        self._headers = {
            'Authorization': 'Bearer %s' % self.api_token
        }

    def get(self, path, **params):
        while True:
            response = requests.get(
                self.base_url + path,
                params=params,
                headers=self._headers
            )

            if not response.status_code or response.status_code > 500:
                continue

            response.raise_for_status()
            return response.json()

    def post(self, path, data={}):
        while True:
            response = requests.post(
                self.base_url + path,
                json=data,
                headers=self._headers
            )

            if response.status_code == 204:
                return True

            if not response.status_code or response.status_code > 500:
                continue

            response.raise_for_status()
            return response.json()

    def delete(self, path):
        while True:
            response = requests.delete(
                self.base_url + path,
                headers=self._headers
            )

            if not response.status_code or response.status_code > 500:
                continue

            response.raise_for_status()
            return True

    def ssh(self, droplet, ssh_key):
        parts = [
            'ssh',
            '-o', 'StrictHostKeyChecking=no',
            'root@%s' % droplet['networks']['v4'][0]['ip_address'],
            '-i', ssh_key
        ]

        proc = subprocess.Popen(parts)
        return proc.wait()

    def run(self, droplet, ssh_key, command):
        parts = [
            'ssh',
            '-o', 'StrictHostKeyChecking=no',
            'root@%s' % droplet['networks']['v4'][0]['ip_address'],
            '-i', ssh_key,
            command
        ]

        proc = subprocess.Popen(parts)
        return proc.wait()
