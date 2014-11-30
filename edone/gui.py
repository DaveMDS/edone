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
from efl.elementary.frame import Frame
from efl.elementary.genlist import Genlist, GenlistItemClass, ELM_LIST_COMPRESS
from efl.elementary.icon import Icon
from efl.elementary.label import Label
from efl.elementary.list import List
from efl.elementary.panes import Panes
from efl.elementary.table import Table
from efl.elementary.segment_control import SegmentControl
from efl.elementary.separator import Separator

from edone.utils import options, theme_resource_get
from edone.tasks import TASKS, load_from_file, save_to_file


EXPAND_BOTH = EVAS_HINT_EXPAND, EVAS_HINT_EXPAND
EXPAND_HORIZ = EVAS_HINT_EXPAND, 0.0
EXPAND_VERT = 0.0, EVAS_HINT_EXPAND
FILL_BOTH = EVAS_HINT_FILL, EVAS_HINT_FILL
FILL_HORIZ = EVAS_HINT_FILL, 0.5
FILL_VERT = 0.5, EVAS_HINT_FILL


def LOG(text):
    print(text)
    # pass


class EdoneWin(StandardWindow):
    def __init__(self):
        # main widget 'pointers'
        self.tasks_list = None
        self.filters = None
        self.task_view = None

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

        b = Button(hbox1, text="Save")
        b.callback_clicked_add(lambda b: self.save())
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
        search.part_text_set('guide', 'search (TODO)')
        search.content_set('end', Icon(search, standard='home', size_hint_min=(16,16)))
        hbox3.pack_end(search)
        search.show()

        sep = Separator(vbox, horizontal=True)
        vbox.pack_end(sep)
        sep.show()

        ### Main horizontal box ###
        hbox = Box(vbox, horizontal=True,
                   size_hint_weight=EXPAND_BOTH, size_hint_align=FILL_BOTH)
        vbox.pack_end(hbox)
        hbox.show()

        # the filters box widget (inside a padding frame)
        self.filters = Filters(hbox)
        fr = Frame(hbox, style='pad_medium', content=self.filters,
                   size_hint_weight=EXPAND_VERT, size_hint_align=FILL_VERT)
        hbox.pack_end(fr)
        fr.show()

        ### the main panes (horiz or vert)
        panes = Panes(hbox, horizontal=not options.horiz_layout,
                      content_left_min_relative_size=0.3,
                      content_right_min_relative_size=0.1,
                      size_hint_weight=EXPAND_BOTH, size_hint_align=FILL_BOTH)
        panes.content_left_size = 1.0
        hbox.pack_end(panes)
        panes.show()

        ### the tasks list ###
        self.tasks_list = TasksList(panes)
        panes.part_content_set("left", self.tasks_list)

        ### the single task view ###
        self.task_view = TaskView(panes)
        panes.part_content_set("right", self.task_view)

        # show the window
        self.resize(800, 600)
        self.show()

    def reload(self):
        load_from_file(options.txt_file)
        self.tasks_list.rebuild()
        self.filters.populate_lists()

    def save(self):
        save_to_file(options.txt_file)


FILTER_STATUS_ALL = 0
FILTER_STATUS_TODO = 1
FILTER_STATUS_DONE = 2

class Filters(Box):
    def __init__(self, parent):
        self.status = FILTER_STATUS_ALL

        Box.__init__(self, parent,
                     size_hint_weight=EXPAND_VERT, size_hint_align=FILL_VERT)

        # status
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
        label = Label(self, text="<b>Projects +</b>", scale=1.4)
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
        label = Label(self, text="<b>Contexts @</b>", scale=1.4)
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
        self.cxts_list.clear()
        self.projs_list.clear()
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
        self.callback_selected_add(self._item_selected_cb)
        self.show()

    def rebuild(self):
        LOG('rebuild tasks list (%d tasks)' % len(TASKS))
        self.clear()
        self.top_widget.task_view.clear()

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

    def update_selected(self):
        if self.selected_item:
            self.selected_item.update()

    def _item_selected_cb(self, gl, item):
        self.top_widget.task_view.update(item.data)

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
        self.task = None
        Entry.__init__(self, parent, line_wrap=ELM_WRAP_MIXED, scrollable=True,
                       size_hint_weight=EXPAND_BOTH, size_hint_align=FILL_BOTH)
        self.part_text_set('guide', 'Select a task to edit')
        self.callback_changed_user_add(self._changed_user_cb)
        self.show()

    def update(self, task=None):
        if task is not None:
            self.task = task
        self.text = self.task.raw_txt

    def clear(self):
        self.task = None
        self.text = None

    def _changed_user_cb(self, en):
        if self.task:
            self.task.raw_txt = self.text
            self.task.parse_from_raw()
            self.top_widget.tasks_list.update_selected()

