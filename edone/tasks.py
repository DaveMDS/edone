#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2015-2018 Davide Andreoli <dave@gurumeditation.it>
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

import os
import datetime


TASKS = []

_notes_path = None
_need_save = False

class Task(object):
    """ Class to describe a single task """

    def __init__(self, raw_text=''):
        self._raw_txt = raw_text
        self._completed = False
        self._text = 'todo'
        self._priority = None  # 'A'
        self._projects = []  # +
        self._contexts = []  # @
        self._creation_date = '2014-12-30'
        self._completion_date = '2014-12-31'

        self._progress = None  # int(0-100)     TAG = prog:XX
        self._note = None      # note file name TAG = note:XXXX.txt
        # self._files = []     # files:

        if raw_text:
            self._parse_from_raw()

    def __repr__(self):
        return '<Task: "%s" +%s @%s>' % (self._raw_txt, self._projects, self._contexts)

    def __getattr__(self, name):
        return getattr(self, '_' + name)

    def __setattr__(self, name, value):
        global _need_save

        if name.startswith('_'):
            object.__setattr__(self, name, value)
        else:
            object.__setattr__(self, '_' + name, value)
            if name == 'raw_txt':
                self._parse_from_raw()
            else:
                self._raw_from_props()
            _need_save = True

    def delete(self):
        global _need_save

        if self._note and os.path.exists(self._note):
            os.remove(self._note)

        TASKS.remove(self)
        _need_save = True

    def create_note_filename(self):
        # create notes folder if needed
        if not os.path.exists(_notes_path):
            os.mkdir(_notes_path)

        # find a free file name
        if self.note is None:
            i = 1
            while True:
                fname = os.path.join(_notes_path, '%03d.txt' % i)
                if not os.path.exists(fname):
                    break
                i += 1

            # store filename triggering _raw_from_props()
            self.note = os.path.join(_notes_path, fname)

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
        self._contexts = [ x for x in words if x[0] == '@' and len(x) > 1 ]
        self._projects = [ x for x in words if x[0] == '+' and len(x) > 1 ]

        # custom attributes
        self._progress = None
        for x in words:
            # completion progress
            if x.startswith('prog:'):
                try:
                    self._progress = int(x.split(':')[1])
                    txt = txt.replace(x, '')
                except: pass

            # note file
            elif x.startswith('note:'):
                try:
                    fname = x.split(':')[1]
                    self._note = os.path.join(_notes_path, fname)
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
            self._raw_txt += ' prog:%d' % self._progress

        # note file
        if self._note is not None:
            self._raw_txt += ' note:%s' % os.path.basename(self._note)


def need_save():
    return _need_save


def load_from_file(path):
    global _notes_path

    print('Loading tasks from file: "%s"' % path)

    _notes_path = path + '.notes'
    del TASKS[:]

    with open(path) as f:
        for line in f:
            t = Task(line.strip())
            TASKS.append(t)


def save_to_file(path):
    global _need_save

    print('Saving tasks to file: "%s"' % path)

    with open(path, 'w') as f:
        for t in TASKS:
            print(t.raw_txt, file=f)
    _need_save = False

