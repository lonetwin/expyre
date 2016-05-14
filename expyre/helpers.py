#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Wrapper functions for the `at` commands"""

import functools
import logging
import os
import re
import subprocess
import time

from collections import namedtuple
from contextlib import contextmanager
from datetime import datetime

try:
    from shutil import which
    atcmd = which('at')
except ImportError:
    try:
        atcmd = subprocess.check_output(('which', 'at')).strip()
    except subprocess.CalledProcessError:
        atcmd = None

log = logging.getLogger('expyre')

# - Object to represent a scheduled expiry job
JobSpec = namedtuple('JobSpec', ('job_id', 'path', 'timestamp', 'conditions'))

# - The expiry shell script where the comments serve to identify the job
# as something that was created by this module.
SCRIPT_TEMPLATE = """
# expyre path: {path}
# expyre conditions: {conditions_string}
#
{conditions}
    {action}
"""

# - Nifty little trick to extract the path and conditions_string
# from the `at` job spec: build the regex using SCRIPT_TEMPLATE above!
SCRIPT_RE = re.compile(SCRIPT_TEMPLATE.format(path=r'(?P<path>.*)',
                                              conditions_string=r'(?P<conditions_string>.*)',
                                              conditions=r'(?P<conditions>.*)',
                                              action=r'(?P<action>.*)$'
                                              ), re.DOTALL)

# - regex to extract job id and time from the stdout right after scheduling a job
jobid_re = re.compile(r'^job (?P<job_id>\d+) at (?P<timespec>.*)$', re.MULTILINE)

# - regex to extract job id and other details from `at -l` listing
job_info_re = re.compile(r'(^\d+)\t(.*) (\w) (\w+)')


def pre_exec_check():
    if not atcmd:
        raise RuntimeError("Could not find `at` command")
    try:
        output = subprocess.check_output('ps -e | grep atd', shell=True).strip()
    except subprocess.CalledProcessError:
        raise RuntimeError("The at daemon (atd) doesn't appear to be running."
                           " Expiry jobs cannot be scheduled or executed if atd is not running")


at_call = functools.partial(subprocess.check_output, preexec_fn=pre_exec_check)


def at_list():
    """List of all `at` scheduled jobs"""
    return [job for job in at_call((atcmd, '-l')).split('\n') if job.strip()]


def at_cat(job_id):
    """Get the script of the scheduled job identified by `job_id`"""
    return at_call((atcmd, '-c', job_id))


def at_rm(job_id):
    """Remove the specified `job_id` from the `at` schedule"""
    return at_call((atcmd, '-r', job_id))


def expire_path(path, timespec, unless_modified=True, unless_accessed=True):
    """Schedule expiry for a path and return the job_id for the scheduled task.

    :param str path: The path to schedule for expiry. Warning: if the path is a
        directory, the path will be removed with the `rm -rf ` command !
    :param timespec: A datetime object or string as recognized by the `at` command.
    :param bool unless_modified: Whether a condition has to be added to the job
        expiry script to expire the path only if it has not been modified since
        it was scheduled for expiry. Default: True
    :param bool unless_accessed: Whether a condition has to be added to the job
        expiry script to expire the path only if it has not been accessed since
        it was scheduled for expiry. Default: True
    :return: `JobSpec` object describing the scheduled expiry job.
    :rtype: JobSpec
    """
    path = os.path.abspath(os.path.expanduser(path))
    timespec = timespec.strftime("%R %F") if isinstance(timespec, datetime) else timespec

    if os.path.isdir(path):
        log.warn('Will execute `rm -rf %s` at %s', path, timespec)
    action = 'rm {} {}'.format('-rf' if os.path.isdir(path) else '', path)

    conditions = []
    as_string = []

    if unless_modified or unless_accessed:
        now = time.time()
        localtime = datetime.fromtimestamp(now)

        for condition, description, option in ((unless_accessed, 'accessed', 'X'),
                                               (unless_modified, 'modified', 'Y')):
            if condition:
                conditions.append('''[ ! "$(stat -c '%{0}' {1})" -gt {2:.0f} ]'''.format(option, path, now))
                as_string.append('unless {0} after {1:%R %F}'.format(description, localtime))
        conditions.append(' &&')

    script = SCRIPT_TEMPLATE.format(path=path,
                                    action=action,
                                    conditions_string=' or '.join(as_string),
                                    conditions=' ||\n'.join(conditions)
                                    )

    process = subprocess.Popen([atcmd, timespec],
                               preexec_fn=pre_exec_check,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT
                               )
    stdout, _ = process.communicate(script)

    log.debug('output: %s', stdout)
    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, atcmd)

    match = jobid_re.search(stdout, re.MULTILINE)
    job_id = match.group('job_id')
    timestamp = datetime.strptime(match.group('timespec'), '%c')
    return JobSpec(job_id, path, timestamp, ' or '.join(as_string))


def get_scheduled_jobs():
    """Return a map of paths to JobSpec for all paths scheduled for expiry.
    """
    jobs = {}
    for job in at_list():
        job_id, timespec, queue, user = re.search(job_info_re, job).groups()
        job_spec = at_cat(job_id)
        match = SCRIPT_RE.search(job_spec)
        if match:
            path, conditions, _, _ = match.groups()
            timestamp = datetime.strptime(timespec, '%c')
            jobs[path] = JobSpec(job_id, path, timestamp, conditions)
    return jobs


def remove_from_schedule(paths):
    assert(isinstance(paths, (list, tuple)))
    scheduled_jobs = get_scheduled_jobs()
    success, faliure = [], []
    for path in paths:
        path = os.path.abspath(os.path.expanduser(path))
        if path not in scheduled_jobs:
            log.debug('%s was not scheduled for expiry, skipping...', path)
            faliure.append(path)
            continue
        job_spec = scheduled_jobs[path]
        log.debug('removing %s with job id %s from expiry schedule', job_spec.path, job_spec.job_id)
        output = at_rm(job_spec.job_id)
        success.append(path)
        log.debug('output: %s', output)
    return success, faliure


@contextmanager
def open_expiring(filename, at, unless_modified=True, unless_accessed=True, *args):
    """A contextmanager that provides a open file descriptor to a file that
    will be scheduled for expiry on exit.

    :param str filename: The file to open and schedule for expiry.
    :param at: A datetime object or string as recognized by the `at` command.
    :param bool unless_modified: Whether a condition has to be added to the job
        expiry script to expire the path only if it has not been modified since
        it was scheduled for expiry. Default: True
    :param bool unless_accessed: Whether a condition has to be added to the job
        expiry script to expire the path only if it has not been accessed since
        it was scheduled for expiry. Default: True
    :param *args: Any additional arguments to be passed on to the `open` builtin.
    :return: An open file object.
    :rtype: file
    """
    try:
        with open(filename, *args) as fd:
            yield fd
    except:
        raise
    else:
        expire_path(filename, at, unless_modified, unless_accessed)
