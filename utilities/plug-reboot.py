#!/usr/bin/env python

import sys
import argparse
import logging
import time

import powerswitch

log = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description='Reboot power switch plugs')
    parser.add_argument(
        'plug', nargs='+',
        help='power plug ID (for example: nps01/1)')
    parser.add_argument(
        '-n', '--num', type=int, default=1,
        help='number of reboots (default: 1)')
    parser.add_argument(
        '-i', '--interval', type=int, default=120,
        help='reboot interval [sec] (default: 120)')
    args = parser.parse_args()

    # Enable logging to console
    logging.basicConfig(level=logging.INFO)

    while (args.num):
        try:
            powerswitch.reboot_plugs(args.plug)
        except powerswitch.Error as err:
            sys.exit(err)
        args.num -= 1
        if args.num:
            log.info('Waiting for next reboot...')
            time.sleep(args.interval)


if __name__ == '__main__':
	#powerswitch._reboot_plug('10.10.0.2', '4')
	#powerswitch.reboot_plugs('10.10.0.2/4')
    main()
