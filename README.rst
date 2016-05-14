expyre
======

A pythonic wrapper over `atd` to schedule deletion of files/directories.

Source code: https://github.com/lonetwin/expyre

Install using pip ``pip install expyre`` or download from https://pypi.python.org/pypi/expyre

What is expyre ?
----------------

``expyre`` is a python module that provides a command line as well as a
``contextmanager`` which enables you to schedule files/directories for deletion
at some point in the future. It does this by relying on the `atd(8)` service for
the scheduling of jobs.

Since usually examples are better than a long README

Command line usage

::

    # - schedule a file for deletion 2 days from now
    $ expyre -p path/to/file0 @now + 2days
    [212] /home/steve/src/venvs/expyre/path/to/file0 will expire at 2016-05-16 19:10

    # - schedule a file for deletion a minute befor new year 2018
    $ expyre --unless-modified -p path/to/file1 @23:59 2017-12-31
    [213] /home/steve/src/venvs/expyre/path/to/file1 will expire at 2017-12-31 23:59

    # - list the current expiry schedule
    $ expyre -l
    /home/steve/src/venvs/expyre/path/to/file1 scheduled to expire at 2017-01-01 19:07 unless modified after 19:07 2016-05-14
    /home/steve/src/venvs/expyre/path/to/file0 scheduled to expire at 2016-05-16 19:10

    # - remove a file from the expiry schedule
    $ expyre -r /home/steve/src/venvs/expyre/path/to/file0
    Successfully removed these paths from expiry list:
    /home/steve/src/venvs/expyre/path/to/file0

Python usage

.. code:: python

    from datetime import datetime, timedelta
    from expyre.helpers import *

    # - as a contextmanager
    filename = '/path/to/file'
    with open_expiring(filename, 'w', at='now + 3days', unless_accessed=True) as fd:
        # - create a file with a scheduled deletion time exactly 3 days from
        # time of creation unless it has been accessed before the deletion time.
        ...

    # - schedule a file for deletion providing time as a string
    expire_path('./path/to/file0', 'now + 2days')
    JobSpec(job_id='216', path='/home/steve/src/venvs/expyre/path/to/file0', timestamp=datetime.datetime(2016, 5, 16, 19, 20), conditions='unless accessed after 19:20 2016-05-14 or unless modified after 19:20 2016-05-14')

    # - schedule a file for deletion providing time as a datetime object
    expire_path('./path/to/file1', (datetime.now() + timedelta(days=3)), unless_modified=True)
    JobSpec(job_id='217', path='/home/steve/src/venvs/expyre/path/to/file1', timestamp=datetime.datetime(2016, 5, 17, 19, 20), conditions='unless accessed after 19:20 2016-05-14 or unless modified after 19:20 2016-05-14')

    # - Get the expiry schedule as a dict
    get_scheduled_jobs()
    {'/home/steve/src/venvs/expyre/path/to/file0': JobSpec(job_id='216', path='/home/steve/src/venvs/expyre/path/to/file0', timestamp=datetime.datetime(2016, 5, 16, 19, 20), conditions='unless accessed after 19:20 2016-05-14 or unless modified after 19:20 2016-05-14'),
     '/home/steve/src/venvs/expyre/path/to/file1': JobSpec(job_id='217', path='/home/steve/src/venvs/expyre/path/to/file1', timestamp=datetime.datetime(2016, 5, 17, 19, 20), conditions='unless accessed after 19:20 2016-05-14 or unless modified after 19:20 2016-05-14')}

    # - remove a file from the expiry schedule
    remove_from_schedule(['/home/steve/src/venvs/expyre/path/to/file0'])
    (['/home/steve/src/venvs/expyre/path/to/file0'], [])


A few things to note
--------------------

    * This has only be tested on my local dev box (Fedora 23 with python 2.7).
      So YMMV. Please do some cursory testing before relying on this tool.
    * Since (afaict), ``atd(8)`` has only minute level precision, the same
      limitation applies to ``expyre``.
    * Directories will be deleted with a ``rm -rf`` option ! So, you need to be
      careful when scheduling those for deletion.
    * The ``--unless_accessed`` and ``--unless_modified`` options to directories
      imply the access time and modification time for the *directory*, not the
      files under them.
    * Please, please, please do report bugs or send in suggestions for
      improvements if you can. This would be greatly appreciated.
    * Patches and code reviews would be even more appreciated.
