#! /usr/bin/env python
"""Console script for websensor."""
import argparse
import importlib
import json
import logging
import sys
from os.path import basename, dirname, join

from utils.utils import drop_to_shell


def init_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    # Add the console handler
    handler_console = logging.StreamHandler()
    format_console = logging.Formatter(
        "%(asctime)s: %(levelname)8s: [%(filename)s:%(funcName)s:%(lineno)d]: "
        "%(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler_console.setFormatter(format_console)
    handler_console.setLevel(logging.DEBUG)
    logger.addHandler(handler_console)


def main():
    """Console script for websensor."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-s', '--short',
        action='store_true',
        help='Run the short mode'
    )
    parser.add_argument(
        '-g', '--generate-secrets-file',
        action='store_true',
        help='Generate an example secrets file'
    )
    parser.add_argument(
        '-l', '--log',
        action='store_true',
        help='Enable logger'
    )
    parser.add_argument('sensor', nargs='?', help='Sensor to use')
    parser.add_argument('args', nargs='*', help='Args for the sensor')
    args = parser.parse_args()

    if args.generate_secrets_file:
        with open(join(dirname(__file__), 'websensor.secrets.example')) \
            as secrets:
            print(secrets.read())
            return(0)
    elif not args.sensor:
        parser.print_usage()
        print("Provide a sensor")
        return(0)

    args.sensor = args.sensor.replace("/", ".")

    if args.log:
        init_logger()

    module = importlib.import_module(f'sensors.{args.sensor}')
    if args.short:
        getattr(module, 'short')(args)
    else:
        return getattr(module, 'main')(args)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
