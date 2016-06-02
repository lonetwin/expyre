#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import unittest
from datetime import datetime, timedelta
try:
    from StringIO import StringIO
except:
    from io import StringIO
try:
    from unittest import mock
except ImportError:
    import mock

from expyre.__main__ import main
from expyre.helpers import JobSpec

class TestMain(unittest.TestCase):

    def setUp(self):
        self.stdout, self.stderr = StringIO(), StringIO()
        sys.stdout, sys.stderr = self.stdout, self.stderr

        self.dummy_job = JobSpec(0, '/path/to/file', datetime.now(), '')

    def tearDown(self):
        self.stdout, self.stderr = None, None
        self.stdout, sys.stderr = sys.__stdout__, sys.__stderr__

    def test_no_args(self):
        with self.assertRaises(SystemExit):
            main()

    def test_conflicting_args(self):
        with self.assertRaises(SystemExit):
            main('--path /path/to/file --list'.split())
        self.assert_('Conflicting options' in self.stderr.getvalue(), self.stderr.getvalue())

        with self.assertRaises(SystemExit):
            main('--reset /path/to/foo --path /path/to/file'.split())
        self.assert_('Conflicting options' in self.stderr.getvalue(), self.stderr.getvalue())

        with self.assertRaises(SystemExit):
            main('--unless-accessed --path /path/to/file --list'.split())
        self.assert_('Conflicting options' in self.stderr.getvalue(), self.stderr.getvalue())

        with self.assertRaises(SystemExit):
            main('--list --reset /path/to/foo'.split())
        self.assert_('Conflicting options' in self.stderr.getvalue(), self.stderr.getvalue())

    def test_no_timespec(self):
        with self.assertRaises(SystemExit):
            main('--unless-modified --unless-accessed --path /path/to/file'.split())
        self.assert_('Missing timespec' in self.stderr.getvalue(), self.stderr.getvalue())

        with self.assertRaises(SystemExit):
            main(['--unless-modified --unless-accessed --path /path/to/file @'])
        self.assert_('Missing timespec' in self.stderr.getvalue(), self.stderr.getvalue())

    def test_no_filelist(self):
        with self.assertRaises(SystemExit):
            main('--unless-modified --unless-accessed now+3days'.split())
        self.assert_('Missing path' in self.stderr.getvalue(), self.stderr.getvalue())

        with self.assertRaises(SystemExit):
            main('--unless-modified --unless-accessed --path @now+3days'.split())
        self.assert_('Missing path' in self.stderr.getvalue(), self.stderr.getvalue())

    def test_invalid_timestamp(self):
        main('-p /path/to/file @invalid'.split())
        self.assertEqual('Timespec not recognized by at command\n', self.stderr.getvalue())

    def test_correct_invocation_expire_path_at_and_quotes(self):
        with mock.patch('expyre.__main__.expire_path', return_value=self.dummy_job) as mocked:
            main(['--unless-modified', '--unless-accessed', '--path', '/path/to/file', '@now + 3 days'])
            mocked.assert_called_with('/path/to/file', 'now + 3 days', True, True)
            self.assertEquals('[0] /path/to/file will expire at {0:%F %R}\n'.format(self.dummy_job.timestamp),
                              self.stdout.getvalue())

    def test_correct_invocation_expire_path_no_at_and_quotes(self):
        with mock.patch('expyre.__main__.expire_path', return_value=self.dummy_job) as mocked:
            main(['--unless-modified', '--unless-accessed', '--path', '/path/to/file', 'now + 3 days'])
            mocked.assert_called_with('/path/to/file', 'now + 3 days', True, True)
            self.assertEquals('[0] /path/to/file will expire at {0:%F %R}\n'.format(self.dummy_job.timestamp),
                              self.stdout.getvalue())

    def test_correct_invocation_expire_path_at_and_no_quotes(self):
        with mock.patch('expyre.__main__.expire_path', return_value=self.dummy_job) as mocked:
            main('--unless-modified --path /path/to/file @now+3days'.split())
            mocked.assert_called_with('/path/to/file', 'now+3days', True, False)
            self.assertEquals('[0] /path/to/file will expire at {0:%F %R}\n'.format(self.dummy_job.timestamp),
                              self.stdout.getvalue())

    def test_correct_invocation_expire_path_no_at_and_no_quotes(self):
        with mock.patch('expyre.__main__.expire_path', return_value=self.dummy_job) as mocked:
            main('--unless-modified --path /path/to/file now+3days'.split())
            mocked.assert_called_with('/path/to/file', 'now+3days', True, False)
            self.assertEquals('[0] /path/to/file will expire at {0:%F %R}\n'.format(self.dummy_job.timestamp),
                              self.stdout.getvalue())

    def test_correct_invocation_remove_from_schedule_single_path(self):
        with mock.patch('expyre.__main__.remove_from_schedule', return_value=[['/path/to/file'], []]) as mocked:
            main(['--reset', '/path/to/file'])
            mocked.assert_called_with(['/path/to/file'])
            self.assertSequenceEqual('Successfully removed these paths from expiry list:\n'
                                     '/path/to/file\n',
                                     sys.stdout.getvalue())

    def test_correct_invocation_remove_from_schedule_multiple_paths(self):
        with mock.patch('expyre.__main__.remove_from_schedule', return_value=[['/path/to/file1'], ['/path/to/file2']]) as mocked:
            main('--reset /path/to/file1 /path/to/file2'.split())
            mocked.assert_called_with(['/path/to/file1', '/path/to/file2'])
            self.assertSequenceEqual('Successfully removed these paths from expiry list:\n'
                                     '/path/to/file1\n'
                                     'Failed to remove these paths from expiry list:\n'
                                     '/path/to/file2\n',
                                     sys.stdout.getvalue())


    def test_correct_invocation_get_scheduled_jobs_no_jobs(self):
        with mock.patch('expyre.__main__.get_scheduled_jobs', return_value={}) as mocked:
            main(['--list'])
            self.assertTrue(mocked.called)
            self.assertSequenceEqual('No paths scheduled for expiry\n', self.stdout.getvalue())

    def test_correct_invocation_get_scheduled_jobs(self):
        with mock.patch('expyre.__main__.get_scheduled_jobs', return_value={'/path/to/file':self.dummy_job}) as mocked:
            main(['--list'])
            self.assertTrue(mocked.called)
            self.assertSequenceEqual('/path/to/file scheduled to expire at {0:%F %R} \n'.format(self.dummy_job.timestamp),
                                     sys.stdout.getvalue())

    def test_correct_invocation_get_scheduled_jobs_multiple(self):
        now = datetime.now()
        later = datetime.now()+timedelta(hours=2)
        earlier = datetime.now()-timedelta(hours=2)

        jobs = {'/path/to/second': JobSpec(0, '/path/to/second', now, ''),
                '/path/to/last':   JobSpec(1, '/path/to/last', later, ''),
                '/path/to/first':  JobSpec(2, '/path/to/first', earlier, '')
                }

        self.maxDiff = None
        with mock.patch('expyre.__main__.get_scheduled_jobs', return_value=jobs) as mocked:
            main(['--list'])
            self.assertTrue(mocked.called)
            self.assertSequenceEqual(
                    ('/path/to/first scheduled to expire at {0:%F %R} \n'
                     '/path/to/second scheduled to expire at {1:%F %R} \n'
                     '/path/to/last scheduled to expire at {2:%F %R} \n').format(earlier, now, later),
                    sys.stdout.getvalue())
