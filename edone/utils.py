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

import os
import pickle
from xdg.BaseDirectory import xdg_config_home, xdg_cache_home


script_path = os.path.dirname(__file__)
config_path = os.path.join(xdg_config_home, 'edone')
config_file = os.path.join(config_path, 'config.pickle')


class Options(object):
    """ Class to contain application settings """
    def __init__(self):
        self.theme_name = 'default'
        self.horiz_layout = False
        self.txt_file = os.path.join(config_path, 'Todo.txt')

    def load(self):
        try:
            # load only attributes (not methods) from the instance saved to disk
            saved = pickle.load(open(config_file, 'rb'))
            for attr in dir(self):
                if attr[0] != '_' and not callable(getattr(self, attr)):
                    if hasattr(saved, attr):
                        setattr(self, attr, getattr(saved, attr))
        except:
            pass

    def save(self):
        # save this whole class instance to file
        with open(config_file, 'wb') as f:
            pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)

options = Options()


def theme_resource_get(fname):
    return os.path.join(script_path, 'themes', options.theme_name, fname)
