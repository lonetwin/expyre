#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" expyre - Python wrapper over `atd` to schedule deletion of files.

Source code: https://github.com/lonetwin/expyre
"""

from setuptools import setup, find_packages

from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name = 'expyre',
    version = '0.1.1',
    description = 'Python wrapper over `atd` to schedule deletion of files.',
    long_description = long_description,
    url = 'https://github.com/lonetwin/expyre',
    author = 'Steven Fernandez',
    author_email = 'steve@lonetwin.net',
    license = 'MIT',
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        ],
    keywords = 'atd, scheduled file deletion',
    packages = find_packages(exclude=['docs', 'tests']),
    entry_points = {
        'console_scripts' : [
            'expyre = expyre.__main__:main',
            ]
        },
    # - tests
    tests_require = ['mock', 'nose'],
    )
