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
    $ expyre -p path/to/file @now + 2days
    [206] /home/steve/src/venvs/expyre/path/to/file will expire at 2016-05-16 15:52

    # - schedule a file for deletion 2 days from now, unless it is modified before then
    $ expyre --unless-modified -p path/to/another_file @now + 2days
    [207] /home/steve/src/venvs/expyre/path/to/another_file will expire at 2016-05-16 15:53

    # - list the current expiry schedule
    $ expyre -l
    /home/steve/src/venvs/expyre/path/to/another_file scheduled to expire at 2016-05-16 15:53 unless modified after 15:53 2016-05-14
    /home/steve/src/venvs/expyre/path/to/file scheduled to expire at 2016-05-16 15:52

    # - remove a file from the expiry schedule
    $ expyre -r /home/steve/src/venvs/expyre/path/to/file
    Successfully removed these paths from expiry list:
    /home/steve/src/venvs/expyre/path/to/file


Python usage

.. code:: python

    filename = '/path/to/file'
    with open_expiring(filename, 'w', at='now + 3days', unless_accessed=True) as fd:
        # - create a file with a scheduled deletion time exactly 3 days from
        # time of creation unless it has been accessed before the deletion time.
        ...

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
