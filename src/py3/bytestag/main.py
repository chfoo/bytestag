'''Command line application entry point'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
from bytestag.client import Client
from bytestag.keys import KeyBytes
import argparse
import bytestag.basedir
import logging
import os.path

_logger = logging.getLogger(__name__)


def main():
    arg_parser = argparse.ArgumentParser(
        description='Runs an instance of a Bytestag server.')
    arg_parser.add_argument('--cache-dir', default=bytestag.basedir.cache_dir,
        help='directory where temporary files are stored')
#    arg_parser.add_argument('--config-dir',
#        default=bytestag.basedir.config_dir,
#        help='directory where configuration files are stored')
#    arg_parser.add_argument('--data-dir', default=bytestag.basedir.data_dir,
#        help='directory where program files and plugins are stored')
    arg_parser.add_argument('--port', type=int, default=0,
        help='port number of the listening server')
    arg_parser.add_argument('--host', default='0.0.0.0',
        help='hostname or IP address of the listening server')
    arg_parser.add_argument('--cache-size', type=int, default=2 ** 36,
        help='maximum size, in bytes, of the cache')
#    arg_parser.add_argument('--max-disk-ratio', type=float, default=0.75,
#        help='maximum free disk space that may be used')
    arg_parser.add_argument('--share-dir', nargs='*',
        help='directory to share')
    arg_parser.add_argument('--known-node',
        help='initial known contact')
    arg_parser.add_argument('--node-id',
        help='node id of this server')
    arg_parser.add_argument('--log-level',
        help='Python logging level')
    arg_parser.add_argument('--log-filename',
        help='Python logging filename')
    arg_parser.add_argument('--initial-scan', default=False,
        action='store_true',
        help='Python logging filename')

    args = arg_parser.parse_args()

    if args.log_level:
        log_conf = dict(level=args.log_level,
            format='%(levelname)s %(name)s %(module)s:%(lineno)d %(message)s')

        if args.log_filename:
            log_conf['filename'] = args.log_filename

        logging.basicConfig(**log_conf)

    if args.known_node:
        known_node_address, known_node_port = args.known_node.split(':', 1)
        known_node_port = int(known_node_port)
        known_node_address = (known_node_address, known_node_port)
    else:
        known_node_address = None

    client = Client(args.cache_dir, known_node_address=known_node_address,
        address=(args.host, args.port), node_id=KeyBytes(args.node_id or True),
        initial_scan=args.initial_scan)

    client.cache_table.max_size = args.cache_size

    if args.share_dir:
        share_dirs = map(os.path.abspath, args.share_dir)
        client.shared_files_table.shared_directories.extend(share_dirs)

    client.start()
    client.join()
