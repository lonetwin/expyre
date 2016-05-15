#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Command-line for the expyre module.
"""
import argparse
import logging
import sys

from expyre import __version__
from .helpers import expire_path, get_scheduled_jobs, remove_from_schedule

log = logging.getLogger('expyre')

def _parse_args(args):
    parser = argparse.ArgumentParser(description="Schedule paths for deletion.", prog='expyre',
                usage="\n  %(prog)s [-h] [--version]"
                      "\n  %(prog)s [-m] [-a] -p path @TIMESPEC"
                      "\n  %(prog)s -l"
                      "\n  %(prog)s -r path")
    parser.add_argument('--version', action='version', version='%(prog)s ' + __version__)
    at_group = parser.add_argument_group('Options for scheduling path expiry')
    atq_group = parser.add_argument_group('Options to query paths scheduled for expiry')
    atrm_group = parser.add_argument_group('Options to remove paths from expiry schedule')

    at_group.add_argument('-m', '--unless-modified', action='store_true', default=False,
            help='Do not expire path if modified before scheduled time')
    at_group.add_argument('-a', '--unless-accessed', action='store_true', default=False,
            help='Do not expire path if accessed before scheduled time')
    at_group.add_argument('-p', '--path', help='Path to schedule for expiry')
    at_group.add_argument('@', metavar='TIMESPEC', nargs=argparse.REMAINDER,
            help='Time specification in the same format as recognized by at(1)')

    atq_group.add_argument('-l', '--list', action='store_true', default=False,
            help='List paths scheduled for expiry')

    atrm_group.add_argument('-r', '--reset', nargs='+', metavar='path',
            help='Remove specified paths from expiry schedule')

    args = parser.parse_args(args or sys.argv[1:])

    # - arguments from only one arg group can be provided at a time
    if any((args.list and any((args.unless_modified, args.unless_accessed, args.path)),
            args.reset and any((args.unless_modified, args.unless_accessed, args.path)),
            args.list and (args.reset is not None),
            )):
        parser.error("Conflicting options provided; "
                     "you can either schedule paths for deletion or list or reset")
    if not (args.list or args.reset):
        # - if the scheduling options were specified, ensure we have
        # both path and timespec
        timespec = ''.join(s.strip("@ ") for s in vars(args)['@'])
        args.timespec = timespec
        if not args.path:
            parser.error('Missing path')
        elif not timespec:
            parser.error('Missing timespec')
    return args


def main(args=None):
    ret = -1
    try:
        args = _parse_args(args or sys.argv[1:])
        if args.list:
            # - list expiry schedule
            jobs = get_scheduled_jobs()
            if not jobs:
                print('No paths scheduled for expiry')
            for job in jobs.values():
                print('{0.path} scheduled to expire at {0.timestamp:%F %R} {0.conditions}'.format(job))
            ret = 0
        elif args.reset:
            # - remove path from expiry schedule
            success, faliure = remove_from_schedule(args.reset)
            print('Successfully removed these paths from expiry list:')
            print('\n'.join(success))
            if faliure:
                print('Failed to remove these paths from expiry list:')
                print('\n'.join(faliure))
            ret = (0 if not faliure else -1)
        else:
            # - schedule path for expiry
            job = expire_path(args.path, args.timespec, args.unless_modified, args.unless_accessed)
            print('[{0.job_id}] {0.path} will expire at {0.timestamp:%F %R}'.format(job))
            ret = 0
    except RuntimeError as exc:
        sys.stderr.write(exc)

    return ret

if __name__ == '__main__':
    main()
