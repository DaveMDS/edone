#!/usr/bin/env python

import sys
from distutils.core import setup


# require python 3
if sys.version_info < (3,2,0):
    print("Your python version is too old. " \
          "Found: %d.%d.%d  (need >= 3.2.0)" % (
          sys.version_info[0], sys.version_info[1], sys.version_info[2]))
    exit(1)


# require efl >= 1.18
from efl import __version_info__ as efl_version
if efl_version < (1,18,0):
    print('Your python-efl version is too old. ' \
          'Found: %d.%d.%d  (need >= 1.18.0)' % (
          efl_version[0], efl_version[1], efl_version[2]))
    exit(1)


from efl.utils.setup import build_extra, build_fdo, build_i18n, uninstall
from edone import __version__


setup(
    name = 'edone',
    version = __version__,
    description = 'Task (todo) manager',
    long_description = 'A complete gui for your Todo.txt files',
    license = "GPLv3",
    author = 'Dave Andreoli',
    author_email = 'dave@gurumeditation.it',
    packages = ['edone'],
    requires = ['efl (>=1.18)', 'xdg'],
    provides = ['edone'],
    scripts = ['bin/edone'],
    package_data = {
        'edone': ['themes/*/*'],
    },
    cmdclass={
        'build': build_extra,
        'build_fdo': build_fdo,
        #  'build_i18n': build_i18n,
        'uninstall': uninstall,
    },
    command_options={
        'install': {'record': ('setup.py', 'installed_files.txt')}
    },
)
