#!/usr/bin/env python3

import os
import tempfile
import subprocess

def main():
    start_port = 8400
    num_clients = 4
    
    procs = []
    temp_dirs = []

    for i in range(num_clients):
        temp_dir = tempfile.TemporaryDirectory(prefix='bytestag-{:04}-'.format(i))
        temp_dirs.append(temp_dir)
        port_num = start_port + i
        
        args = ['xterm', '-title', 'Client {}'.format(i), '-e', 
            'python3', '-m', 'bytestag', '--log-level=INFO',
            '--host=127.0.0.1', '--port={}'.format(port_num), 
            '--cache-dir', temp_dir.name, '--initial-scan',
#            '--log-filename', '{}/log'.format(temp_dir.name),
            ]
        
        if i != 0:
            args.append('--known-node=127.0.0.1:{}'.format(start_port))
        
        if i != 0 and i >= num_clients - 1:
            args.extend(['--share-dir', '../test_data/'])
        
        new_env = dict(os.environ)
        new_env['PYTHONPATH'] = '{}:src/py3/'.format(new_env.get('PYTHONPATH', ''))

        p = subprocess.Popen(args, env=new_env)

        procs.append(p)

    for p in procs:
        p.wait()


if __name__ == '__main__':
    main()
