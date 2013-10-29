# -*- coding: utf-8 -*-

import unittest
import sys
import os
import types

import launchd

launchdtestplist = dict(
          Disabled=False,
          Label="testlaunchdwrapper_python",
          Nice=-15,
          OnDemand=True,
          ProgramArguments=["/bin/bash", "-c", "echo 'Hello World' && exit 0"],
          RunAtLoad=True,
          ServiceDescription="runs a sample command",
          ServiceIPC=False,
          )


class LaunchctlTestCase(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)

    def tearDown(self):
        unittest.TestCase.tearDown(self)

    @unittest.skipUnless(sys.platform.startswith("darwin"), "requires OS X")
    def test_examples(self):
        activejobs = [job for job in launchd.jobs() if job.pid is not None]
        inactivejobs = [job for job in launchd.jobs() if job.pid is None]
        errorjobs = [job for job in launchd.jobs() if job.laststatus != 0 and job.laststatus is not None]
        ondemandjobs = [job for job in launchd.jobs() if job.properties['OnDemand'] is True]

    @unittest.skipUnless(sys.platform.startswith("darwin"), "requires OS X")
    def test_launchd_jobs(self):
        jobs = launchd.jobs()
        self.assertFalse(isinstance(jobs, list))  # it's a generator!
        count = 0
        for job in jobs:
            count += 1
            self.assertTrue(isinstance(job, launchd.LaunchdJob))
            self.assertTrue(isinstance(job.pid, (int, types.NoneType)))
            self.assertTrue(isinstance(job.laststatus, (int, types.NoneType)))
            self.assertTrue(isinstance(job.properties, dict))
            self.assertTrue(isinstance(job.plistfilename, (str, types.NoneType)))
            # the next 2 fail sometimes due to short lived processes that
            # have disappeared by the time we reach this test
            self.assertTrue('PID' in job.properties if job.pid is not None else True)
            self.assertTrue('PID' not in job.properties if job.pid is None else True)
        self.assertTrue(count > 0)

    @unittest.skipUnless(sys.platform.startswith("darwin"), "requires OS X")
    def test_launchd_jobs_and_plist(self):
        for job in launchd.jobs():
            if job.plistfilename is not None:
                self.assertTrue(os.path.isfile(job.plistfilename))

    @unittest.skipUnless(sys.platform.startswith("darwin"), "requires OS X")
    def test_launchd_lazy_constructor(self):
        # we assume that com.apple.Finder always exists and that it is always
        # running and always has a laststatus. Hmmmm.
        label = "com.apple.Finder"
        job = launchd.LaunchdJob(label)
        self.assertTrue(job.exists())
        self.assertEqual(None, job._pid)
        self.assertEqual(None, job._laststatus)
        self.assertEqual(None, job._properties)
        job.refresh()
        self.assertNotEqual(None, job._pid)
        self.assertNotEqual(None, job._laststatus)
        self.assertNotEqual(None, job._properties)

        job = launchd.LaunchdJob(label, load=True)
        self.assertTrue(job.exists())
        self.assertNotEqual(None, job._pid)
        self.assertNotEqual(None, job._laststatus)
        self.assertNotEqual(None, job._properties)

        # let's do the same with something invalid:
        label = "com.apple.Nonexistant-bogus-entry"
        job = launchd.LaunchdJob(label, 1, 2)
        self.assertEqual(1, job.pid)
        self.assertEqual(2, job.laststatus)
        self.assertFalse(job.exists())
        self.assertRaises(ValueError, job.refresh)
        # these properties are reset during refresh()
        self.assertEqual(None, job.pid)
        self.assertEqual(None, job.laststatus)
