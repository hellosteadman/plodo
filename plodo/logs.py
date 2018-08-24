import subprocess
from threading import Thread


def get_remote_logs(key_filename, *ips, tail=False):
    for ip in ips:
        def run():
            parts = [
                'ssh',
                '-o', 'StrictHostKeyChecking=no',
                'root@%s' % ip,
                '-i', key_filename,
                'tail'
            ]

            if tail:
                parts.append('-f')

            parts.append('/var/log/upstart/*.log')
            proc = subprocess.Popen(parts)
            proc.wait()

        thread = Thread(target=run)
        thread.start()
