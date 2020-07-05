#! /usr/bin/env python
"""Console script for websensor."""
import argparse
import logging
import sys
from os.path import basename
from pydoc import locate



LOGGER = logging.getLogger()
LOGGER.setLevel(logging.DEBUG)
# Add the console handler
handler_console = logging.StreamHandler()
format_console = logging.Formatter(
    basename(__file__) +": %(asctime)s: %(levelname)8s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
handler_console.setFormatter(format_console)
handler_console.setLevel(logging.DEBUG)
LOGGER.addHandler(handler_console)


def main():
    """Console script for websensor."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-s', '--short',
        action='store_true',
        help='Run the short mode'
    )
    parser.add_argument(
        '-l', '--log',
        action='store_true',
        help='Enable logger'
    )
    parser.add_argument('sensor', help='Sensor to use')
    parser.add_argument('args', nargs='*')
    args = parser.parse_args()

    args.sensor.replace("/", ".")

#    print(government.pf.main())
    import sensors.finance.pf
    sensors.finance.pf.short(args)
    klass = locate(f'sensors.{args.sensor}')
    if not klass:
        print("No such sensor")
        return -1
    if args.short:
        getattr(klass, 'short')(args)
    else:
        return getattr(klass, 'main')(args)


if __name__ == "__main__":
    sys.exit(main())  # pragma: no cover
