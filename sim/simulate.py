#!/usr/bin/env python3

import argparse
import os
import path
import subprocess
import tempfile

def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--log-level', default='WARNING', type=str,
        help='Python log level')
    arg_parser.add_argument('--main-server', default=False,
        action='store_true', help='Start a main coordinator server')
    arg_parser.add_argument('--empty-clients', default=0, type=int,
        help='Start number of clients with no data to share')
    arg_parser.add_argument('--data-clients', default=0, type=int,
        help='Start number of clients with data to share')

    args = arg_parser.parse_args()

    procs = []
    temp_dirs = []

    def get_default_proc_args(title=''):
        return ['xterm', '-title', 'Client {}'.format(title), '-e',
            'python3', '-m', 'bytestag', '--log-level', args.log_level
            ]

    def run_proc(args):
        new_env = dict(os.environ)
        new_env['PYTHONPATH'] = '{}:{}'.format(new_env.get('PYTHONPATH', ''),
            path.src_path)

        p = subprocess.Popen(args, env=new_env)

        return p


    if args.main_server:
        temp_dir = tempfile.TemporaryDirectory(prefix='bytestag-MAIN')
        temp_dirs.append(temp_dir)

        proc_args = get_default_proc_args(title='MAIN')
        proc_args.extend(['--cache-size=0', '--host=127.0.0.1', '--port=8400',
            '--cache-dir', temp_dir.name])

        proc = run_proc(proc_args)

        procs.append(proc)

    for i in range(args.data_clients):
        temp_dir = tempfile.TemporaryDirectory(
            prefix='bytestag-DATA-{:04}-'.format(i))
        temp_dirs.append(temp_dir)

        proc_args = get_default_proc_args(title='DATA-{}'.format(i))

        proc_args.extend(['--initial-scan', '--host=127.0.0.1',
            '--share-dir', '../../test_data/', '--known-node=127.0.0.1:8400',
            '--cache-dir', temp_dir.name])

        proc = run_proc(proc_args)

        procs.append(proc)

    for i in range(args.empty_clients):
        temp_dir = tempfile.TemporaryDirectory(
            prefix='bytestag-DATA-{:04}-'.format(i))
        temp_dirs.append(temp_dir)

        proc_args = get_default_proc_args(title='DATA-{}'.format(i))

        proc_args.extend(['--host=127.0.0.1',
            '--known-node=127.0.0.1:8400',
            '--cache-dir', temp_dir.name])

        proc = run_proc(proc_args)

        procs.append(proc)


    for p in procs:
        p.wait()


if __name__ == '__main__':
    main()
