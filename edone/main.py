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
import sys

from efl import elementary as elm
from edone.utils import options, config_path
from edone.gui import EdoneWin

# setup efl logging
import logging
elog = logging.getLogger("efl")
elog.addHandler(logging.StreamHandler())
elog.setLevel(logging.INFO)


def main():

    # load config and create necessary folders and files
    options.load()
    if not os.path.exists(config_path):
        os.makedirs(config_path)
    if not os.path.exists(options.txt_file):
        with open(options.txt_file, 'a') as f:
            print('(A) Welcome to Etodo', file=f)

    # create the main window and load the todo file
    elm.init()
    win = EdoneWin()
    win.reload()

    # enter the mainloop
    elm.run()

    # mainloop done, shutdown
    elm.shutdown()
    options.save()

    return 0


if __name__ == "__main__":
    sys.exit(main())

