#!/usr/bin/env python

from distutils.core import setup

setup(
    name = 'edone',
    version = '0.9', # Don't forget to change also in gui.py
    description = 'Getting-Things-Done',
    long_description = 'Getting-Things-Done written in Python-EFL',
    license = "GNU GPL",
    author = 'Dave Andreoli',
    author_email = 'dave@gurumeditation.it',
    packages = ['edone'],
    requires = ['efl', 'xdg'],
    provides = ['edone'],
    package_data = {
        'edone': ['themes/*/*'],
    },
    scripts = ['bin/edone'],
    data_files = [
        ('share/applications', ['data/edone.desktop']),
        ('share/icons', ['data/icons/256x256/edone.png']),
        ('share/icons/hicolor/256x256/apps', ['data/icons/256x256/edone.png']),
    ]
)
