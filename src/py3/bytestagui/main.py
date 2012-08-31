'''Application entry point'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
import argparse
import datetime
import logging
import os.path


def main(default_gui='qt'):
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--log-level', help='Python log level')
    arg_parser.add_argument('--enable-disk-log', action='store_true',
        default=False,
        help='Enable logging to home dir')
    arg_parser.add_argument('--gui-toolkit', default=default_gui,
        help='Which GUI Toolkit to use (gtk or qt)')
    args = arg_parser.parse_args()

    log_args = {}

    if args.log_level:
        log_args['level'] = args.log_level

    if args.enable_disk_log:
        log_args['filename'] = os.path.join(os.path.expanduser('~'),
            'bytestag_{}.log'.format(
                datetime.datetime.utcnow().isoformat().replace(':', '_')))

    logging.basicConfig(**log_args)

    if args.gui_toolkit.lower() == 'qt':
        from bytestagui.qt.controllers.app import Application as QTApplication
        Application = QTApplication
    else:
        from bytestagui.gtk.controllers.app import Application as GTKApplication
        Application = GTKApplication

    app = Application()
    app.run()
