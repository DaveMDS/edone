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
import sys

from efl import elementary as elm
from edone.utils import options, config_path
from edone.gui import EdoneWin


def main():

    # load config and create necessary folders
    options.load()
    if not os.path.exists(config_path):
        os.makedirs(config_path)

    # create the main window
    elm.init()
    win = EdoneWin()

    # try to load a repo, from command-line or cwd (else show the RepoSelector)
    # RepoSelector(win, args.repo or os.getcwd())

    # enter the mainloop
    elm.run()

    # mainloop done, shutdown
    elm.shutdown()
    options.save()

    return 0


if __name__ == "__main__":
    sys.exit(main())

