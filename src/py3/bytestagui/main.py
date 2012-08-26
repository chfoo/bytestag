'''Application entry point'''
# This file is part of Bytestag.
# Copyright © 2012 Christopher Foo <chris.foo@gmail.com>.
# Licensed under GNU GPLv3. See COPYING.txt for details.
import argparse
import logging


def main():
    global GTKApplication, QTApplication

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--log-level', help='Python log level')
    arg_parser.add_argument('--gui-toolkit', default='gtk',
        help='Which GUI Toolkit to use (gtk or qt)')
    args = arg_parser.parse_args()

    if args.log_level:
        logging.basicConfig(level=args.log_level)

    if args.gui_toolkit.lower() == 'qt':
        from bytestagui.qt.controllers.app import Application as QTApplication
        Application = QTApplication
    else:
        from bytestagui.gtk.controllers.app import Application as GTKApplication
        Application = GTKApplication

    app = Application()
    app.run()
