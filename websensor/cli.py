"""Console script for websensor."""
import argparse
import sys
from pydoc import locate


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
