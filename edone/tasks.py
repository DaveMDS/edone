#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2015 Davide Andreoli <dave@gurumeditation.it>
#
# This file is part of Edone.
#
# Edone is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
#
# Edone is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Edone.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, print_function

import datetime


TASKS = []

class Task(object):
    """ Class to describe a single task """

    def __init__(self, raw_text=''):
        self._raw_txt = raw_text
        self._completed = False
        self._text = 'todo'
        self._priority = None # 'A'
        self._projects = [] # +
        self._contexts = [] # @
        self._creation_date = '2014-12-30'
        self._completion_date = '2014-12-31'

        self._progress = None
        # self._notes = None # note:
        # self._files = []   # files:

        if raw_text:
            self._parse_from_raw()

    def __repr__(self):
        return '<Task: "%s" +%s @%s>' % (self._raw_txt, self._projects, self._contexts)

    def __getattr__(self, name):
        return getattr(self, '_' + name)

    def __setattr__(self, name, value):
        if name.startswith('_'):
            object.__setattr__(self, name, value)
        else:
            print("SET", name, value)
            object.__setattr__(self, '_' + name, value)
            if name == 'raw_txt':
                self._parse_from_raw()
            else:
                self._raw_from_props()

            # TODO NEED SAVE

    def _parse_from_raw(self):
        txt = self._raw_txt

        # completed
        if txt.startswith('x '):
            self._completed = True
            txt = txt[2:]
        else:
            self._completed = False

        # priority
        if txt[0] == '(' and txt[1].isupper() and txt[2] == ')' and txt[3] == ' ':
            self._priority = txt[1]
            txt = txt[4:]
        else:
            self._priority = None

        # two dates (format: 2014-12-30)
        date1 = date2 = None
        try:
            date1 = datetime.datetime.strptime(txt[:9], '%Y-%m-%d')
            txt = txt[9:]
            date2 = datetime.datetime.strptime(txt[:9], '%Y-%m-%d')
            txt = txt[9:]
        except:
            pass

        if date1 and date2:
            self._completion_date = date1
            self._creation_date = date2
        elif date1:
            self._creation_date = date1
            self._completion_date = None
        else:
            self._creation_date = None
            self._completion_date = None

        # contexts & projects lists
        words = txt.split()
        self._contexts = [ x[1:] for x in words if x[0] == '@' and len(x) > 1 ]
        self._projects = [ x[1:] for x in words if x[0] == '+' and len(x) > 1 ]

        # custom attributes
        self._progress = None
        for x in words:
            # completion progress
            if x.startswith('PROG:'):
                try:
                    self._progress = int(x.split(':')[1])
                    txt = txt.replace(x, '')
                except: pass

        self._text = txt

    def _raw_from_props(self):
        self._raw_txt = ''

        # completed
        if self._completed:
            self._raw_txt += 'x '

        # priority
        if self._priority:
            self._raw_txt += '(%s) ' % self._priority

        # dates
        if self._completion_date:
            self._raw_txt += '%s ' % self._completion_date.strftime('%Y-%m-%d')
        if self._creation_date:
            self._raw_txt += '%s ' % self._creation_date.strftime('%Y-%m-%d')

        # clean text
        self._raw_txt += self._text

        # completion progress
        if self._progress is not None:
            self._raw_txt += ' PROG:%d' % self._progress


def load_from_file(path):
    print('Loading tasks from file: "%s"' % path)

    del TASKS[:]

    with open(path) as f:
        for line in f:
            t = Task(line.strip())
            TASKS.append(t)

    for t in TASKS:
        print(t)


def save_to_file(path):
    print('Saving tasks to file: "%s"' % path)

    with open(path, 'w') as f:
        for t in TASKS:
            print(t.raw_txt, file=f)

