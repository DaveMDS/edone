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
# import os
# import pickle
# from xdg.BaseDirectory import xdg_config_home, xdg_cache_home


TASKS = []

class Task(object):
    """ Class to describe a single task """
    def __init__(self, raw_text=''):
        self.raw_txt = raw_text
        self.completed = False
        self.text = 'todo'
        self.priority = None # 'A'
        self.projects = [] # +
        self.contexts = [] # @
        self.creation_date = '2014-12-30'
        self.completion_date = '2014-12-31'

        self.progress = None
        # self.notes = None # note:
        # self.files = []   # files:

        if raw_text:
            self.parse_from_raw()

    def __repr__(self):
        return '<Task: "%s" +%s @%s>' % (self.raw_txt, self.projects, self.contexts)

    def parse_from_raw(self):
        txt = self.raw_txt

        # completed
        if txt.startswith('x '):
            self.completed = True
            txt = txt[2:]
        else:
            self.completed = False

        # priority
        if txt[0] == '(' and txt[1].isupper() and txt[2] == ')' and txt[3] == ' ':
            self.priority = txt[1]
            txt = txt[4:]
        else:
            self.priority = None

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
            self.completion_date = date1
            self.creation_date = date2
        elif date1:
            self.creation_date = date1
            self.completion_date = None
        else:
            self.creation_date = None
            self.completion_date = None

        # contexts & projects lists
        words = txt.split()
        self.contexts = [ x[1:] for x in words if x[0] == '@' and len(x) > 1 ]
        self.projects = [ x[1:] for x in words if x[0] == '+' and len(x) > 1 ]

        # custom attributes
        self.progress = None
        for x in words:
            # completion progress
            if x.startswith('PROG:'):
                try:
                    self.progress = int(x.split(':')[1])
                    txt = txt.replace(x, '')
                except: pass

        self.text = txt

    def raw_from_props(self):
        self.raw_txt = ''

        # completed
        if self.completed:
            self.raw_txt += 'x '

        # priority
        if self.priority:
            self.raw_txt += '(%s) ' % self.priority

        # dates
        if self.completion_date:
            self.raw_txt += '%s ' % self.completion_date.strftime('%Y-%m-%d')
        if self.creation_date:
            self.raw_txt += '%s ' % self.creation_date.strftime('%Y-%m-%d')

        # clean text
        self.raw_txt += self.text

        # completion progress
        if self.progress is not None:
            self.raw_txt += ' PROG:%d' % self.progress


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

