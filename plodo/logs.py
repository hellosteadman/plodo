import subprocess
from threading import Thread


def get_remote_logs(key_filename, *ips, tail=False):
    for ip in ips:
        def run():
            parts = [
                'ssh',
                'root@%s' % ip,
                '-i', key_filename,
                'journalctl'
            ]

            if tail:
                parts.append('-f')

            proc = subprocess.Popen(parts)
            proc.wait()

        thread = Thread(target=run)
        thread.start()
