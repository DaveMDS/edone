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
from operator import attrgetter
        
from efl import elementary as elm
from efl.evas import Rectangle, EVAS_HINT_EXPAND, EVAS_HINT_FILL
from efl.elementary.window import StandardWindow
from efl.elementary.box import Box
from efl.elementary.button import Button
from efl.elementary.colorselector import Colorselector
from efl.elementary.entry import Entry, ELM_WRAP_MIXED
from efl.elementary.fileselector import Fileselector
from efl.elementary.frame import Frame
from efl.elementary.genlist import Genlist, GenlistItemClass, \
    ELM_LIST_COMPRESS, ELM_GENLIST_ITEM_GROUP
from efl.elementary.icon import Icon
from efl.elementary.label import Label
from efl.elementary.list import List
from efl.elementary.menu import Menu
from efl.elementary.panes import Panes
from efl.elementary.popup import Popup
from efl.elementary.progressbar import Progressbar
from efl.elementary.table import Table
from efl.elementary.segment_control import SegmentControl
from efl.elementary.separator import Separator

from edone.utils import options, theme_resource_get, tag_color_get
from edone.tasks import Task, TASKS, load_from_file, save_to_file, need_save


EXPAND_BOTH = EVAS_HINT_EXPAND, EVAS_HINT_EXPAND
EXPAND_HORIZ = EVAS_HINT_EXPAND, 0.0
EXPAND_VERT = 0.0, EVAS_HINT_EXPAND
FILL_BOTH = EVAS_HINT_FILL, EVAS_HINT_FILL
FILL_HORIZ = EVAS_HINT_FILL, 0.5
FILL_VERT = 0.5, EVAS_HINT_FILL

DONE_FONT = 'color=#AAA strikethrough=on strikethrough_color=#222'


def LOG(text):
    print(text)
    # pass


class EdoneWin(StandardWindow):
    def __init__(self):
        # main widget 'pointers'
        self.tasks_list = None
        self.filters = None
        self.task_view = None
        self.search_entry = None
        self.main_panes = None

        # the window
        StandardWindow.__init__(self, "edone", "Edone")
        self.callback_delete_request_add(lambda o: self.safe_quit())

        # main vertical box
        vbox = Box(self, size_hint_weight=EXPAND_BOTH)
        self.resize_object_add(vbox)
        vbox.show()

        ### Header ###
        hbox1 = Box(vbox, horizontal=True)
        fr = Frame(vbox, style='outdent_bottom', content=hbox1,
                   size_hint_weight=EXPAND_HORIZ, size_hint_align=FILL_HORIZ)
        vbox.pack_end(fr)
        fr.show()

        # menu button
        m = OptionsMenu(hbox1)
        hbox1.pack_end(m)
        m.show()

        # new task button
        b = Button(hbox1, text='New Task')
        b.content = Icon(hbox1, standard='add')
        b.callback_clicked_add(lambda b: self.task_add())
        hbox1.pack_end(b)
        b.show()

        # title
        title = Label(hbox1, text="Getting Things Done", scale=2.0,
                      size_hint_weight=EXPAND_HORIZ, size_hint_align=FILL_HORIZ)
        hbox1.pack_end(title)
        title.show()

        # search entry
        en = Entry(hbox1, single_line=True, scrollable=True,
                   size_hint_weight=EXPAND_HORIZ, size_hint_align=FILL_HORIZ)
        en.part_text_set('guide', 'search')
        en.callback_changed_user_add(self._search_changed_user_cb)
        en.content_set('end', Icon(en, standard='find', size_hint_min=(20,20)))
        hbox1.pack_end(en)
        en.show()
        self.search_entry = en

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
        self.main_panes = panes

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
        self.filters.populate_lists()
        self.tasks_list.rebuild()

    def save(self, and_quit=False):
        save_to_file(options.txt_file)
        if and_quit is True:
            elm.exit()

    def safe_quit(self):
        if need_save() is False:
            elm.exit()
        else:
            pp = Popup(self, text="You have unsave changes, if you don't save now all your recent modification will be lost.")
            pp.part_text_set('title,text', 'Save changes to your txt file?')

            btn = Button(pp, text='Close without saving')
            btn.callback_clicked_add(lambda b: elm.exit())
            pp.part_content_set('button1', btn)

            btn = Button(pp, text='Cancel')
            btn.callback_clicked_add(lambda b: pp.delete())
            pp.part_content_set('button2', btn)

            btn = Button(pp, text='Save')
            btn.callback_clicked_add(lambda b: self.save(True))
            pp.part_content_set('button3', btn)

            pp.show()

    def task_add(self):
        t = Task('New item')
        TASKS.append(t)
        it = self.tasks_list.item_add(t)
        it.selected = True
        self.task_view.focus = True
        self.task_view.select_all()

    def _search_changed_user_cb(self, en):
        self.tasks_list.rebuild()


class OptionsMenu(Button):
    def __init__(self, parent):
        self._menu = None
        Button.__init__(self, parent, text='Menu',
                        content=Icon(parent, standard='home'))
        self.callback_pressed_add(self._button_pressed_cb)

    def _button_pressed_cb(self, btn):
        # close the menu if it is visible yet
        if self._menu and self._menu.visible:
            self._menu.delete()
            self._menu = None
            return

        # build a new menu
        m = Menu(self.top_widget)
        self._menu = m

        # main actions (save, reload, quit)
        it = m.item_add(None, 'Save', 'folder',
                        lambda m,i: self.top_widget.save())
        if need_save() is False:
            it.disabled = True

        m.item_add(None, 'Reload', 'refresh',
                   lambda m,i: self.top_widget.reload())

        m.item_add(None, 'Quit', 'exit',
                   lambda m,i: self.top_widget.safe_quit())

        m.item_separator_add()

        # group by >
        it_groupby = m.item_add(None, 'Group by')
        icon = 'arrow_right' if options.group_by == 'none' else None
        m.item_add(it_groupby, 'None', icon,
                   lambda m,i: self._groupby_set('none'))
        icon = 'arrow_right' if options.group_by == 'prj' else None
        m.item_add(it_groupby, 'Projects', icon,
                   lambda m,i: self._groupby_set('prj'))
        icon = 'arrow_right' if options.group_by == 'ctx' else None
        m.item_add(it_groupby, 'Contexts', icon,
                   lambda m,i: self._groupby_set('ctx'))

        # sort by >
        it_sortby = m.item_add(None, 'Sort by')
        icon = 'arrow_right' if options.sort_by == 'none' else None
        m.item_add(it_sortby, 'No sort', icon,
                   lambda m,i: self._sortby_set('none'))
        icon = 'arrow_right' if options.sort_by == 'pri' else None
        m.item_add(it_sortby, 'Priority', icon,
                   lambda m,i: self._sortby_set('pri'))

        # layout >
        it_layout = m.item_add(None, 'Layout')
        icon = 'arrow_right' if options.horiz_layout is False else None
        m.item_add(it_layout, 'Vertical', icon,
                   lambda m,i: self._layout_set(False))
        icon = 'arrow_right' if options.horiz_layout is True else None
        m.item_add(it_layout, 'Horizontal', icon,
                   lambda m,i: self._layout_set(True))

        # Todo.txt file...
        m.item_add(None, 'Todo.txt file...', None,
                   lambda m,i: self._file_change())

        # show the menu
        x, y, w, h = self.geometry
        m.move(x, y + h)
        m.show()

    def _layout_set(self, horiz):
        options.horiz_layout = horiz
        self.top_widget.main_panes.horizontal = not horiz

    def _groupby_set(self, group):
        options.group_by = group
        self.top_widget.tasks_list.rebuild()

    def _sortby_set(self, sort):
        options.sort_by = sort
        self.top_widget.tasks_list.rebuild()

    def _file_change(self):
        # hack to make popup respect min_size
        rect = Rectangle(self.parent.evas, size_hint_min=(400,400))
        tb = Table(self.parent)
        tb.pack(rect, 0, 0, 1, 1)

        # show the fileselector inside a popup
        popup = Popup(self.top_widget, content=tb)
        popup.part_text_set('title,text', 'Choose the Todo.txt file to use')
        popup.show()

        # the fileselector widget
        fs = Fileselector(popup, is_save=False, expandable=False,
                        size_hint_weight=EXPAND_BOTH, size_hint_align=FILL_BOTH)
        fs.callback_activated_add(self._file_change_done, popup)
        fs.callback_done_add(self._file_change_done, popup)
        try:
            fs.selected = options.txt_file
        except:
            fs.path = os.path.expanduser('~')
        fs.show()
        tb.pack(fs, 0, 0, 1, 1)

    def _file_change_done(self, fs, new_path, popup):
        if new_path is not None:
            options.txt_file = new_path
            self.top_widget.reload()
        popup.delete()


class Filters(Box):
    def __init__(self, parent):
        Box.__init__(self, parent,
                     size_hint_weight=EXPAND_VERT, size_hint_align=FILL_VERT)

        # status (view: all, todo or done)
        seg = SegmentControl(self)
        for name, val in ('All','all'),('Todo','todo'),('Done','done'):
            it = seg.item_add(None, name)
            it.data['view'] = val
            it.selected = True if options.view == val else False
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

    @property
    def all_contexts(self):
        return [ item.text for item in self.cxts_list.items ]

    @property
    def all_projects(self):
        return [ item.text for item in self.projs_list.items ]

    def _status_changed_cb(self, seg, item):
        options.view = item.data['view']
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
            name = '@' + c
            color = options.tag_colors.get(name, options.def_ctx_color)
            rect = ColorRect(self, color, name)
            it = self.cxts_list.item_append(name)
            it.part_content_set('start', rect)
        self.cxts_list.go()

        for p in sorted(set(projects)):
            name = '+' + p
            color = options.tag_colors.get(name, options.def_prj_color)
            rect = ColorRect(self, color, name)
            it = self.projs_list.item_append(name)
            it.part_content_set('start', rect)
        self.projs_list.go()


class ColorRect(Frame):
    def __init__(self, parent, color, tag_name):
        Frame.__init__(self, parent, style='pad_small', propagate_events=False)
        self._rect = Rectangle(self.evas, color=color)
        self._rect.on_mouse_down_add(lambda o,i: self._popup_build())
        self.content = self._rect
        self._tag_name = tag_name

    def _popup_build(self):
        popup = Popup(self.top_widget)
        popup.part_text_set('title,text',
                            'Choose the color for %s' % self._tag_name)
        popup.callback_block_clicked_add(lambda p: popup.delete())

        cs = Colorselector(popup, color=self._rect.color)
        cs.callback_changed_add(lambda s: setattr(rect, 'color', cs.color))
        popup.content = cs

        rect = Rectangle(popup.evas, color=self._rect.color)
        frame = Frame(popup, style='pad_small', content=rect)
        popup.part_content_set('button1', frame)

        bt = Button(popup, text='Accept')
        bt.callback_clicked_add(self._popup_accept_cb, popup, cs)
        popup.part_content_set('button2', bt)

        bt = Button(popup, text='Cancel')
        bt.callback_clicked_add(lambda b: popup.delete())
        popup.part_content_set('button3', bt)

        popup.show()

    def _popup_accept_cb(self, obj, popup, colorselector):
        self._rect.color = colorselector.color
        options.tag_colors[self._tag_name] = self._rect.color
        popup.delete()


class TasksList(Genlist):
    def __init__(self, parent):
        self.itc = GenlistItemClass(item_style="default_style",
                        decorate_item_style='full',
                        text_get_func=self._gl_text_get,
                        content_get_func=self._gl_content_get)
        self.itcg = GenlistItemClass(item_style="group_index",
                        text_get_func=self._gl_g_text_get)
        Genlist.__init__(self, parent, mode=ELM_LIST_COMPRESS, homogeneous=True)
        self.callback_selected_add(self._item_selected_cb)
        self.callback_longpressed_add(lambda gl,it: TaskPropsMenu(gl, it.data))
        self.callback_activated_add(lambda gl,it: self._it_edit_start(it))
        self.callback_item_unfocused_add(lambda gl,it: self._it_edit_end(True))
        self.show()
        self.groups = {} # key: group_name  data: genlist_group_item

    def rebuild(self):
        LOG('rebuild tasks list (%d tasks)' % len(TASKS))
        self.clear()
        self.groups = {}
        self.top_widget.task_view.clear()

        filters = self.top_widget.filters
        ctx_set = filters.context_filter
        prj_set = filters.project_filter
        search = self.top_widget.search_entry.text

        # first add all the group items (if grouping enable)
        if options.group_by == 'prj':
            for group_name in filters.all_projects + ['+']:
                self.groups[group_name] = self.item_append(self.itcg,
                                    group_name, flags=ELM_GENLIST_ITEM_GROUP)
        elif options.group_by == 'ctx':
            for group_name in filters.all_contexts + ['@']:
                self.groups[group_name] = self.item_append(self.itcg,
                                    group_name, flags=ELM_GENLIST_ITEM_GROUP)

        if options.sort_by == 'pri':
            sort_key = attrgetter('raw_txt')
        else:
            sort_key = None

        for t in sorted(TASKS, key=sort_key):
            if (options.view == 'done' and not t.completed) or \
               (options.view == 'todo' and t.completed):
                continue

            f1 = True if ctx_set is None else \
                    len(ctx_set.intersection(t.contexts)) > 0

            f2 = True if prj_set is None else \
                    len(prj_set.intersection(t.projects)) > 0

            f3 = True if not search else \
                    search.lower() in t.raw_txt.lower()

            if f1 and f2 and f3:
                self.item_add(t)

        # and finally delete empty group items
        for name, item in self.groups.iteritems():
            # TODO this should be: item.subitems_count()... but it does not work
            if len(item.subitems_get()) == 0:
                item.delete()

    def item_add(self, t):
        # no grouping (just append the item)
        if options.group_by == 'none':
            it = self.item_append(self.itc, t)
        # group by projects (append in every projects)
        elif options.group_by == 'prj':
            if len(t.projects) > 0:
                for p in t.projects:
                    it = self.item_append(self.itc, t, self.groups['+'+p])
            else:
                it = self.item_append(self.itc, t, self.groups['+'])
        # group by contexts (append in every contexts)
        elif options.group_by == 'ctx':
            if len(t.contexts) > 0:
                for c in t.contexts:
                    it = self.item_append(self.itc, t, self.groups['@'+c])
            else:
                it = self.item_append(self.itc, t, self.groups['@'])
        return it

    def update_selected(self):
        if self.selected_item:
            self.selected_item.update()

    def _item_selected_cb(self, gl, item):
        self.top_widget.task_view.update(item.data)

    def _it_edit_start(self, item):
        item.decorate_mode = ('edit', True)

    def _it_edit_end(self, save):
        item = self.decorated_item
        if item is not None:
            if save:
                task = item.data
                task.raw_txt = item.part_content_get('elm.swallow.content').text
            item.decorate_mode = ('edit', False)
            item.selected = True
            item.update()

    def _gl_g_text_get(self, obj, part, group_name):
        if group_name == '+': return 'Tasks without any projects'
        if group_name == '@': return 'Tasks without any contexts'
        return group_name

    def _gl_text_get(self, obj, part, task):
        # apply tag colors
        words = []
        for word in task.text.split():
            if word.startswith(('@', '+')) and len(word) > 1:
                words.append('<font font_weight=bold color=%s>%s</font>' %
                             (tag_color_get(word, hex=True), word))
            else:
                words.append(word)
        formatted = ' '.join(words)

        # strikethrough todo tasks
        if task.completed:
            return '<font %s>%s</font>' % (DONE_FONT, formatted)
        else:
            return formatted

    def _gl_content_get(self, obj, part, task):
        if part == 'elm.swallow.content':
            # this is the full style for the 'edit' mode
            en = Entry(self, editable=True, single_line=True,
                       scrollable=True, propagate_events=False,
                       text=task.raw_txt)
            en.callback_activated_add(lambda e: self._it_edit_end(True))
            en.callback_aborted_add(lambda e: self._it_edit_end(False))
            en.show()
            en.cursor_end_set() # TODO move cursor to the mouse pos
            en.focus = True
            return en

        elif part == 'elm.swallow.icon':
            if task.priority is not None:
                fname = task.priority + '.png'
                return Icon(self, file=theme_resource_get(fname))

        elif part == 'elm.swallow.end':
            if task.progress is not None:
                val = float(task.progress) / 100
                return Progressbar(self, span_size=100, value=val)


class TaskPropsMenu(Menu):
    def __init__(self, parent, task):
        self._task = task
        Menu.__init__(self, parent)

        # done/todo
        if task.completed:
            self.item_add(None, 'Mark as Todo', None,
                          lambda m,i: self._completed_set(False))
        else:
            self.item_add(None, 'Mark as Done', None,
                          lambda m,i: self._completed_set(True))

        # priority
        it_prio = self.item_add(None, 'Priority')
        for p in ('A', 'B', 'C', 'D', 'E'):
            icon = 'arrow_right' if task.priority == p else None
            self.item_add(it_prio, p, icon, self._priority_cb)

        # completion progress
        it_prog = self.item_add(None, 'Progress')
        for p in range(0, 101, 10):
            if task.progress is not None and p <= task.progress < p + 10:
                icon = 'arrow_right'
            else:
                icon = None
            self.item_add(it_prog, '%d %%' % p, icon, self._progress_cb)

        # delete task
        self.item_separator_add()
        self.item_add(None, 'Delete task', None, self._confirm_delete)

        # show the menu at mouse position
        x, y = self.evas.pointer_canvas_xy_get()
        self.move(x + 2, y)
        self.show()

    def _completed_set(self, completed):
        self._task.completed = completed
        self.top_widget.tasks_list.update_selected()

    def _priority_cb(self, m, item):
        self._task.priority = item.text
        self.top_widget.tasks_list.update_selected()

    def _progress_cb(self, m, item):
        val = int(item.text[:-2])
        self._task.progress = val
        self._task.completed = True if val == 100 else False
        self.top_widget.tasks_list.update_selected()

    def _confirm_delete(self, m, item):
        pp = Popup(self.parent, text=self._task.text)
        pp.part_text_set('title,text', 'Confirm task deletion?')

        btn = Button(pp, text='Cancel')
        btn.callback_clicked_add(lambda b: pp.delete())
        pp.part_content_set('button1', btn)

        btn = Button(pp, text='Delete Task')
        btn.callback_clicked_add(self._delete_confirmed, pp)
        pp.part_content_set('button2', btn)

        pp.show()

    def _delete_confirmed(self, b, popup):
        popup.delete()
        self._task.delete()
        self.top_widget.tasks_list.rebuild()


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
            self.top_widget.tasks_list.update_selected()

