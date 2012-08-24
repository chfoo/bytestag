from bytestagui.controllers.app import Application
import argparse
import logging


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--log-level', help='Python log level')
    args = arg_parser.parse_args()

    if args.log_level:
        logging.basicConfig(level=args.log_level)

    app = Application()
