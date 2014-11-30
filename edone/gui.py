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

from efl import elementary as elm
from efl.evas import EVAS_HINT_EXPAND, EVAS_HINT_FILL
from efl.elementary.window import StandardWindow
from efl.elementary.box import Box
from efl.elementary.button import Button
from efl.elementary.entry import Entry, ELM_WRAP_MIXED
from efl.elementary.genlist import Genlist, GenlistItemClass, ELM_LIST_COMPRESS
from efl.elementary.icon import Icon
from efl.elementary.label import Label
from efl.elementary.list import List
from efl.elementary.panes import Panes
from efl.elementary.table import Table
from efl.elementary.segment_control import SegmentControl
from efl.elementary.separator import Separator

from edone.utils import options, theme_resource_get
from edone.tasks import TASKS, load_from_file


EXPAND_BOTH = EVAS_HINT_EXPAND, EVAS_HINT_EXPAND
EXPAND_HORIZ = EVAS_HINT_EXPAND, 0.0
FILL_BOTH = EVAS_HINT_FILL, EVAS_HINT_FILL
FILL_HORIZ = EVAS_HINT_FILL, 0.5


def LOG(text):
    print(text)
    # pass


class EdoneWin(StandardWindow):
    def __init__(self):
        # main widget 'pointers'
        self.tasks_list = None
        self.filters = None

        # the window
        StandardWindow.__init__(self, "edone", "Edone")
        self.autodel_set(True)
        self.callback_delete_request_add(lambda o: elm.exit())

        # main vertical box
        vbox = Box(self, size_hint_weight=EXPAND_BOTH)
        self.resize_object_add(vbox)
        vbox.show()

        ### Header ###
        table = Table(vbox, size_hint_weight=EXPAND_HORIZ,
                      size_hint_align=FILL_HORIZ)
        vbox.pack_end(table)
        table.show()

        # buttons
        hbox1 = Box(table, horizontal=True, align=(0.0, 0.0),
                    size_hint_weight=EXPAND_HORIZ, size_hint_align=(0.0, 0.5))
        table.pack(hbox1, 0, 0, 1, 1)
        hbox1.show()

        b = Button(hbox1, text="Save", disabled=True)
        hbox1.pack_end(b)
        b.show()

        b = Button(hbox1, text="Reload")
        b.callback_clicked_add(lambda b: self.reload())
        hbox1.pack_end(b)
        b.show()

        b = Button(hbox1, text="Add", disabled=True)
        hbox1.pack_end(b)
        b.show()
        
        # title
        hbox2 = Box(table, horizontal=True, align=(0.0, 0.0),
                    size_hint_weight=EXPAND_HORIZ, size_hint_align=FILL_HORIZ)
        table.pack(hbox2, 1, 0, 1, 1)
        hbox2.show()

        title = Label(vbox, text="Getting Things Done", scale=2.5)
        hbox2.pack_end(title)
        title.show()

        # search entry
        hbox3 = Box(table, horizontal=True, align=(1.0, 0.0),
                    size_hint_weight=EXPAND_HORIZ, size_hint_align=FILL_HORIZ)
        table.pack(hbox3, 2, 0, 1, 1)
        hbox3.show()
        
        search = Entry(hbox3, single_line=True, scrollable=True,
                       size_hint_weight=EXPAND_HORIZ, size_hint_align=FILL_HORIZ)
        search.part_text_set('guide', 'search')
        search.content_set('end', Icon(search, standard='home', size_hint_min=(16,16)))
        hbox3.pack_end(search)
        search.show()


        sep = Separator(vbox, horizontal=True)
        vbox.pack_end(sep)
        sep.show()

        ### Main content (left + right panes) ###
        panes = Panes(vbox, content_left_size=0.25,
                      size_hint_weight=EXPAND_BOTH, size_hint_align=FILL_BOTH)
        vbox.pack_end(panes)
        panes.show()

        # the what-to-view options
        self.filters = Filters(panes)
        panes.part_content_set("left", self.filters)

        ### the second panes (horiz or vert)
        panes2 = Panes(panes, content_left_size=0.8,
                       horizontal=not options.horiz_layout,
                       size_hint_weight=EXPAND_BOTH, size_hint_align=FILL_BOTH)
        panes.part_content_set("right", panes2)
        panes2.show()

        ### the tasks list ###
        self.tasks_list = TasksList(panes2)
        panes2.part_content_set("left", self.tasks_list)

        ### the single task view ###
        task_view = TaskView(panes2)
        panes2.part_content_set("right", task_view)

        # show the window
        self.resize(800, 600)
        self.show()

    def reload(self):
        load_from_file(options.txt_file)
        self.tasks_list.rebuild()
        self.filters.populate_lists()


FILTER_STATUS_ALL = 0
FILTER_STATUS_TODO = 1
FILTER_STATUS_DONE = 2

class Filters(Box):
    def __init__(self, parent):
        self.status = FILTER_STATUS_ALL

        Box.__init__(self, parent, align=(0.5, 0.0))

        seg = SegmentControl(self)
        it = seg.item_add(None, "All")
        it.data['status'] = FILTER_STATUS_ALL
        it.selected = True
        it = seg.item_add(None, "Todo")
        it.data['status'] = FILTER_STATUS_TODO
        it = seg.item_add(None, "Done")
        it.data['status'] = FILTER_STATUS_DONE
        seg.callback_changed_add(self._status_changed_cb)
        self.pack_end(seg)
        seg.show()

        # @Projects list
        label = Label(self, text="+Projects")
        self.pack_end(label)
        label.show()

        self.projs_list = List(self, multi_select=True,
                               size_hint_weight=EXPAND_BOTH,
                               size_hint_align=FILL_BOTH)
        self.projs_list.callback_selected_add(self._list_selection_changed_cb)
        self.projs_list.callback_unselected_add(self._list_selection_changed_cb)
        self.pack_end(self.projs_list)
        self.projs_list.show()
        
        # @Contexts list
        label = Label(self, text="@Contexts")
        self.pack_end(label)
        label.show()

        self.cxts_list = List(self, multi_select=True,
                              size_hint_weight=EXPAND_BOTH,
                              size_hint_align=FILL_BOTH)
        self.cxts_list.callback_selected_add(self._list_selection_changed_cb)
        self.cxts_list.callback_unselected_add(self._list_selection_changed_cb)
        self.pack_end(self.cxts_list)
        self.cxts_list.show()

        self.show()

    @property
    def context_filter(self):
        L = [ item.text[1:] for item in  self.cxts_list.selected_items ]
        return set(L) if L else None

    @property
    def project_filter(self):
        L = [ item.text[1:] for item in  self.projs_list.selected_items ]
        return set(L) if L else None
    
    def _status_changed_cb(self, seg, item):
        self.status = item.data['status']
        self.top_widget.tasks_list.rebuild()

    def _list_selection_changed_cb(self, li, it):
        self.top_widget.tasks_list.rebuild()

    def populate_lists(self):
        contexts = []
        projects = []
        for t in TASKS:
            contexts.extend(t.contexts)
            projects.extend(t.projects)

        for c in sorted(set(contexts)):
            self.cxts_list.item_append('@' + c)
        self.cxts_list.go()

        for p in sorted(set(projects)):
            self.projs_list.item_append('+' + p)
        self.projs_list.go()



class TasksList(Genlist):
    def __init__(self, parent):
        self.itc = GenlistItemClass(item_style="default_style",
                        text_get_func=self._gl_text_get,
                        content_get_func=self._gl_content_get)
        Genlist.__init__(self, parent, mode=ELM_LIST_COMPRESS, homogeneous=True)
        self.show()

    def rebuild(self):
        LOG('rebuild tasks list (%d tasks)' % len(TASKS))
        self.clear()
        filters = self.top_widget.filters

        for t in TASKS:
            if (filters.status == FILTER_STATUS_DONE and not t.completed) or \
               (filters.status == FILTER_STATUS_TODO and t.completed):
                continue

            st = filters.context_filter
            f1 = True if st is None else len(st.intersection(t.contexts)) > 0

            st = filters.project_filter
            f2 = True if st is None else len(st.intersection(t.projects)) > 0

            if f1 and f2:
                self.item_append(self.itc, t)

    def _gl_text_get(self, obj, part, task):
        print("TEXT_GET (%s) %s" % (part, task))
        if task.completed:
            return '<font color=#AAA strikethrough=on strikethrough_color=#222>' + task.text + '</font>'
        else:
            return task.text

    def _gl_content_get(self, obj, part, task):
        print("CONTENT_GET (%s)" % part)
        if task.priority is None:
            return None
        if part == 'elm.swallow.icon':
            fname = task.priority + '.png'
            return Icon(self, file=theme_resource_get(fname))
        return None


class TaskView(Entry):
    def __init__(self, parent):
        Entry.__init__(self, parent, line_wrap=ELM_WRAP_MIXED, scrollable=True,
                       size_hint_weight=EXPAND_BOTH, size_hint_align=FILL_BOTH)

        self.text = "asdasdasd"

        self.show()
