#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import time
import unittest
from datetime import datetime, timedelta
from tempfile import mkstemp

from expyre.helpers import expire_path
from expyre.helpers import get_scheduled_jobs
from expyre.helpers import open_expiring
from expyre.helpers import remove_from_schedule


class TestOpenExpiring(unittest.TestCase):

    def setUp(self):
        fd, self.filename = mkstemp()
        os.close(fd)

    def tearDown(self):
        os.unlink(self.filename)
        remove_from_schedule([self.filename])

    def test_open_expiring_default(self):
        """Test open_expiring contextmanager in default read mode"""
        with open_expiring(self.filename, at='now + 3days') as fd:
            self.assertIsInstance(fd, file)
            self.assertFalse(fd.closed)
            self.assertEqual(fd.mode, 'r')

        expected_expiry = datetime.fromtimestamp(time.mktime(time.localtime())) + timedelta(days=3)
        scheduled_for_expiry = get_scheduled_jobs()

        self.assertTrue(self.filename in scheduled_for_expiry, scheduled_for_expiry)

        actual_expiry = scheduled_for_expiry[self.filename].timestamp
        # XXX atd only has only minute level precision
        self.assertLessEqual((expected_expiry - actual_expiry).seconds, 60)

    def test_garbled_time(self):
        self.assertRaisesRegexp(RuntimeError, 'Timespec not recognized',
                                expire_path, self.filename, 'now+1hr')
