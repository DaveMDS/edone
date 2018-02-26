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
from operator import attrgetter
from itertools import chain

from efl import elementary as elm
from efl.evas import Rectangle, EXPAND_BOTH, EXPAND_HORIZ, EXPAND_VERT, \
                     FILL_BOTH, FILL_HORIZ, FILL_VERT

from edone.utils import options, theme_resource_get, tag_color_get
from edone.tasks import Task, TASKS, load_from_file, save_to_file, need_save
from edone import __version__ as VERSION



DONE_FONT = 'color=#AAA strikethrough=on strikethrough_color=#222'
INFO = """
<subtitle>Info</subtitle><br>
<hilight>Edone</hilight> is fully compliant with the <hilight>Todo.txt</hilight> specifications.<br>
This basically means that your todo items are stored in a <b>simple and readable text file</b> and you can use any other compliant client to read/edit your tasks.<br>

<br><subtitle>Usage tips</subtitle><br>
1. To added new <hilight>+Project</hilight> or <hilight>@Context</hilight> just type them in the task, prefixed by the <hilight>+</hilight> or the <hilight>@</hilight> symbol.<br>
2. You can change the <b>color of tags</b> clicking on the small colored rectangle.<br>
3. Select one ore more +Project or @Context in the side lists to filter the tasks.<br>
4. <b>Double-click</b> a task to edit.<br>
5. <b>Right-click</b> (or longpress) a task to change it's properties.<br>
6. Put your Todo.txt file in your <hilight>Dropbox</hilight> folder to keep your tasks in sync with other device/apps.<br>

<br><subtitle>License</subtitle><br>
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.<br><br>
This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.<br><br>
You should have received a copy of the GNU General Public License along with this program.  If not, see http://www.gnu.org/licenses/.<br><br>
"""

class SafeIcon(elm.Icon):
    def __init__(self, parent, icon_name, **kargs):
        elm.Icon.__init__(self, parent, **kargs)
        try:
            self.standard = icon_name
        except:
            print("ERROR: Cannot find icon: '%s'" % icon_name)


class EdoneWin(elm.StandardWindow):
    def __init__(self):
        # main widget 'pointers'
        self.tasks_list = None
        self.filters = None
        self.task_note = None
        self.search_entry = None
        self.main_panes = None

        # the window
        elm.StandardWindow.__init__(self, "edone", "Edone")
        self.callback_delete_request_add(lambda o: self.safe_quit())
        # self.focus_highlight_enabled = True

        # main vertical box
        vbox = elm.Box(self, size_hint_weight=EXPAND_BOTH)
        self.resize_object_add(vbox)
        vbox.show()

        ### Header ###
        hbox1 = elm.Box(vbox, horizontal=True)
        fr = elm.Frame(vbox, style='outdent_bottom', content=hbox1,
                       size_hint_weight=EXPAND_HORIZ, size_hint_align=FILL_HORIZ)
        vbox.pack_end(fr)
        fr.show()

        # menu button
        m = OptionsMenu(hbox1)
        hbox1.pack_end(m)
        m.show()

        # new task button
        b = elm.Button(hbox1, text='New Task', focus_allow=False)
        b.content = SafeIcon(hbox1, 'list-add')
        b.callback_clicked_add(lambda b: self.task_add())
        hbox1.pack_end(b)
        b.show()

        # title
        title = elm.Label(hbox1, text="Getting Things Done", scale=2.0,
                          size_hint_weight=EXPAND_HORIZ,
                          size_hint_align=FILL_HORIZ)
        hbox1.pack_end(title)
        title.show()

        # search entry
        en = elm.Entry(hbox1, single_line=True, scrollable=True,
                       size_hint_weight=EXPAND_HORIZ, size_hint_align=FILL_HORIZ)
        en.part_text_set('guide', 'search')
        en.callback_changed_user_add(self._search_changed_user_cb)
        en.content_set('icon', SafeIcon(en, 'edit-find', size_hint_min=(16,16)))
        hbox1.pack_end(en)
        en.show()
        self.search_entry = en

        ### Main horizontal box ###
        hbox = elm.Box(vbox, horizontal=True,
                       size_hint_weight=EXPAND_BOTH, size_hint_align=FILL_BOTH)
        vbox.pack_end(hbox)
        hbox.show()

        # the filters box widget (inside a padding frame)
        self.filters = Filters(hbox)
        fr = elm.Frame(hbox, style='pad_medium', content=self.filters,
                       size_hint_weight=EXPAND_VERT, size_hint_align=FILL_VERT)
        hbox.pack_end(fr)
        fr.show()

        ### the main panes (horiz or vert)
        panes = elm.Panes(hbox, horizontal=not options.horiz_layout,
                          content_left_min_relative_size=0.3,
                          content_right_min_relative_size=0.1,
                          size_hint_weight=EXPAND_BOTH,
                          size_hint_align=FILL_BOTH)
        panes.content_left_size = 1.0
        hbox.pack_end(panes)
        panes.show()
        self.main_panes = panes

        ### the tasks list ###
        self.tasks_list = TasksList(panes)
        panes.part_content_set("left", self.tasks_list)

        ### the single task view ###
        self.task_note = TaskNote(panes)
        panes.part_content_set("right", self.task_note)

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
            pp = elm.Popup(self, text="You have unsave changes, if you don't save now all your recent modification will be lost.")
            pp.part_text_set('title,text', 'Save changes to your txt file?')

            btn = elm.Button(pp, text='Close without saving')
            btn.callback_clicked_add(lambda b: elm.exit())
            pp.part_content_set('button1', btn)

            btn = elm.Button(pp, text='Cancel')
            btn.callback_clicked_add(lambda b: pp.delete())
            pp.part_content_set('button2', btn)

            btn = elm.Button(pp, text='Save')
            btn.callback_clicked_add(lambda b: self.save(True))
            pp.part_content_set('button3', btn)

            pp.show()

    def task_add(self):
        t = Task('A new task')
        TASKS.append(t)
        self.tasks_list.item_add(t, start_editing=True)

    def _search_changed_user_cb(self, en):
        self.tasks_list.rebuild()


class OptionsMenu(elm.Button):
    def __init__(self, parent):
        self._menu = None
        elm.Button.__init__(self, parent, text='Menu', focus_allow=False,
                            content=SafeIcon(parent, 'user-home'))
        self.callback_pressed_add(self._button_pressed_cb)

    def _button_pressed_cb(self, btn):
        # close the menu if it is visible yet
        if self._menu and self._menu.visible:
            self._menu.delete()
            self._menu = None
            return

        # build a new menu
        m = elm.Menu(self.top_widget)
        self._menu = m

        # main actions (save, reload, quit)
        it = m.item_add(None, 'Save', 'document-save',
                        lambda m,i: self.top_widget.save())
        if need_save() is False:
            it.disabled = True

        m.item_add(None, 'Reload', 'view-refresh',
                   lambda m,i: self.top_widget.reload())

        m.item_add(None, 'Quit', 'window-close',
                   lambda m,i: self.top_widget.safe_quit())

        m.item_add(None, 'Info and help', 'help-about',
                   lambda m,i: InfoWin(self.top_widget))

        # Todo.txt file...
        m.item_separator_add()
        m.item_add(None, 'Choose Todo.txt file', None,
                   lambda m,i: self._file_change())
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
        tb = elm.Table(self.parent)
        tb.pack(rect, 0, 0, 1, 1)

        # show the fileselector inside a popup
        popup = elm.Popup(self.top_widget, content=tb)
        popup.part_text_set('title,text', 'Choose the Todo.txt file to use')
        popup.show()

        # the fileselector widget
        fs = elm.Fileselector(popup, is_save=False, expandable=False,
                              size_hint_weight=EXPAND_BOTH,
                              size_hint_align=FILL_BOTH)
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


class Filters(elm.Box):
    def __init__(self, parent):
        self._freezed = False  # used in populate to not trigger callbacks
        elm.Box.__init__(self, parent,
                         size_hint_weight=EXPAND_VERT, size_hint_align=FILL_VERT)

        # status (view: all, todo or done)
        seg = elm.SegmentControl(self, focus_allow=False)
        for name, val in ('All','all'),('Todo','todo'),('Done','done'):
            it = seg.item_add(None, name)
            it.data['view'] = val
            it.selected = True if options.view == val else False
        seg.callback_changed_add(self._status_changed_cb)
        self.pack_end(seg)
        seg.show()

        # @Projects list
        label = elm.Label(self, text="<b>Projects +</b>", scale=1.4)
        self.pack_end(label)
        label.show()

        self.projs_list = elm.List(self, multi_select=True, focus_allow=False,
                                   size_hint_weight=EXPAND_BOTH,
                                   size_hint_align=FILL_BOTH)
        self.projs_list.callback_selected_add(self._list_selection_changed_cb)
        self.projs_list.callback_unselected_add(self._list_selection_changed_cb)
        self.pack_end(self.projs_list)
        self.projs_list.show()
        
        # @Contexts list
        label = elm.Label(self, text="<b>Contexts @</b>", scale=1.4)
        self.pack_end(label)
        label.show()

        self.cxts_list = elm.List(self, multi_select=True, focus_allow=False,
                                  size_hint_weight=EXPAND_BOTH,
                                  size_hint_align=FILL_BOTH)
        self.cxts_list.callback_selected_add(self._list_selection_changed_cb)
        self.cxts_list.callback_unselected_add(self._list_selection_changed_cb)
        self.pack_end(self.cxts_list)
        self.cxts_list.show()

        self.show()

    @property
    def context_filter(self):
        L = [ item.text for item in self.cxts_list.selected_items ]
        return set(L) if L else None

    @property
    def project_filter(self):
        L = [ item.text for item in self.projs_list.selected_items ]
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
        if not self._freezed:
            self.top_widget.tasks_list.rebuild()

    def populate_lists(self):
        tags = {} # key: tag_name  val: num_tasks
        selected = [ it.text for it in chain(self.cxts_list.selected_items,
                                             self.projs_list.selected_items) ]

        for task in TASKS:
            for name in chain(task.projects, task.contexts):
                tags[name] = tags[name] + 1 if name in tags else 1

        self._freezed = True
        self.cxts_list.clear()
        self.projs_list.clear()
        for name, num in sorted(tags.items()):
            rect = ColorRect(self, tag_color_get(name), name)
            num = elm.Label(self, text=str(num), style='marker')
            if name.startswith('+'):
                it = self.projs_list.item_append(name, rect, num)
            else:
                it = self.cxts_list.item_append(name, rect, num)
            if name in selected:
                it.selected = True
        self._freezed = False


class ColorRect(elm.Frame):
    def __init__(self, parent, color, tag_name):
        elm.Frame.__init__(self, parent, style='pad_small',
                           propagate_events=False)
        self._rect = Rectangle(self.evas, color=color)
        self._rect.on_mouse_down_add(lambda o,i: self._popup_build())
        self.content = self._rect
        self._tag_name = tag_name

    def _popup_build(self):
        popup = elm.Popup(self.top_widget)
        popup.part_text_set('title,text',
                            'Choose the color for %s' % self._tag_name)
        popup.callback_block_clicked_add(lambda p: popup.delete())

        cs = elm.Colorselector(popup, color=self._rect.color)
        cs.callback_changed_add(lambda s: setattr(rect, 'color', cs.color))
        popup.content = cs

        rect = Rectangle(popup.evas, color=self._rect.color)
        frame = elm.Frame(popup, style='pad_small', content=rect)
        popup.part_content_set('button1', frame)

        bt = elm.Button(popup, text='Accept')
        bt.callback_clicked_add(self._popup_accept_cb, popup, cs)
        popup.part_content_set('button2', bt)

        bt = elm.Button(popup, text='Cancel')
        bt.callback_clicked_add(lambda b: popup.delete())
        popup.part_content_set('button3', bt)

        popup.show()

    def _popup_accept_cb(self, obj, popup, colorselector):
        self._rect.color = colorselector.color
        options.tag_colors[self._tag_name] = self._rect.color
        popup.delete()


class TasksList(elm.Genlist):
    def __init__(self, parent):
        self.itc = elm.GenlistItemClass(item_style="default_style",
                                        text_get_func=self._gl_text_get,
                                        content_get_func=self._gl_content_get)
        self.itcg = elm.GenlistItemClass(item_style="group_index",
                                         text_get_func=self._gl_g_text_get)
        elm.Genlist.__init__(self, parent, mode=elm.ELM_LIST_COMPRESS,
                             homogeneous=True)
        self.callback_selected_add(self._item_selected_cb)
        try: # TODO remove the try once 1.13 is released
            self.callback_clicked_right_add(self._item_clicked_right_cb)
        except: pass
        self.callback_longpressed_add(self._item_clicked_right_cb)
        self.callback_activated_add(lambda gl,it: self._task_edit_start(it.data))
        self.show()
        self.groups = {} # key: group_name  data: genlist_group_item

    def rebuild(self):
        self.clear()
        self.groups = {}
        self.top_widget.task_note.clear()

        filters = self.top_widget.filters
        ctx_set = filters.context_filter
        prj_set = filters.project_filter
        search = self.top_widget.search_entry.text

        # first add all the group items (if grouping enable)
        if   options.group_by == 'prj': L = filters.all_projects + ['+']
        elif options.group_by == 'ctx': L = filters.all_contexts + ['@']
        else:                           L = []
        for group_name in L:
            git = self.item_append(self.itcg, group_name,
                                   flags=elm.ELM_GENLIST_ITEM_GROUP)
            git.select_mode = elm.ELM_OBJECT_SELECT_MODE_DISPLAY_ONLY
            self.groups[group_name] = git

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
        for name, item in self.groups.items():
            # TODO this should be: item.subitems_count()... but it does not work
            if len(item.subitems_get()) == 0:
                item.delete()

    def item_add(self, t, start_editing=False):
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
        # start editing if requested
        if start_editing:
            it.selected = True
            self._task_edit_start(t)

    def update_selected(self):
        if self.selected_item:
            self.selected_item.update()

    def _item_clicked_right_cb(self, gl, item):
        item.selected = True
        TaskPropsMenu(gl, item.data)

    def _item_selected_cb(self, gl, item):
        self.top_widget.task_note.update(item.data)

    def _task_edit_start(self, task):
        pp = elm.Popup(self.top_widget)
        pp.part_text_set('title,text', 'Edit task')

        en = elm.Entry(pp, editable=True, single_line=True, scrollable=True,
                       text=task.raw_txt)
        en.callback_activated_add(lambda e: self._task_edit_end(task, en, pp))
        en.callback_aborted_add(lambda e: pp.delete())
        pp.part_content_set('default', en)

        b = elm.Button(pp, text='Cancel')
        b.callback_clicked_add(lambda b: pp.delete())
        pp.part_content_set('button1', b)

        b = elm.Button(pp, text='Accept')
        b.callback_clicked_add(lambda b: self._task_edit_end(task, en, pp))
        pp.part_content_set('button2', b)

        pp.show()

        en.cursor_begin_set()
        en.cursor_selection_begin()
        en.cursor_end_set()
        en.cursor_selection_end()

    def _task_edit_end(self, task, entry, popup):
        new_raw = entry.text
        if new_raw:
            task.raw_txt = entry.text
            popup.delete()
            self.update_selected()
            self.top_widget.filters.populate_lists()

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

        if part == 'elm.swallow.icon':
            if task.priority is not None:
                fname = task.priority + '.png'
                return elm.Icon(self, file=theme_resource_get(fname))

        elif part == 'elm.swallow.end':
            ends = []

            if task.progress is not None:
                val = float(task.progress) / 100
                ends.append(elm.Progressbar(self, span_size=100, value=val))

            if task.note is not None:
                ends.append(elm.Icon(self, file=theme_resource_get('note.png'),
                                     size_hint_min=(20,20)))

            if ends:
                box = elm.Box(self, horizontal=True)
                for widget in ends:
                    widget.show()
                    box.pack_end(widget)
                return box


class TaskPropsMenu(elm.Menu):
    def __init__(self, parent, task):
        self._task = task
        elm.Menu.__init__(self, parent)

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
        self.item_add(None, 'Delete task', 'delete', self._confirm_delete)

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
        pp = elm.Popup(self.top_widget, text=self._task.text)
        pp.part_text_set('title,text', 'Confirm task deletion?')

        btn = elm.Button(pp, text='Cancel')
        btn.callback_clicked_add(lambda b: pp.delete())
        pp.part_content_set('button1', btn)

        btn = elm.Button(pp, text='Delete Task')
        btn.callback_clicked_add(self._delete_confirmed, pp)
        pp.part_content_set('button2', btn)

        pp.show()

    def _delete_confirmed(self, b, popup):
        popup.delete()
        self.top_widget.task_note.clear()
        self._task.delete()
        self.top_widget.tasks_list.rebuild()
        self.top_widget.filters.populate_lists()


class TaskNote(elm.Entry):
    GUIDE1 = 'Select a task and click here to add additional notes to the task.'
    GUIDE2 = 'Click here to add additional notes to the task.'
    def __init__(self, parent):
        self.task = None
        elm.Entry.__init__(self, parent, scrollable=True, disabled=True,
                           size_hint_weight=EXPAND_BOTH,
                           size_hint_align=FILL_BOTH)
        self.part_text_set('guide', self.GUIDE1)
        self.callback_clicked_add(self._clicked_cb)
        self.callback_unfocused_add(self._unfocused_cb)
        self.show()

    def update(self, task=None):
        if task is not None:
            self.task = task

        self.part_text_set('guide', self.GUIDE2 if self.task else self.GUIDE1)

        if self.task and self.task.note:
            try:
                self.file_set(self.task.note, elm.ELM_TEXT_FORMAT_PLAIN_UTF8)
            except:
                pass
            self.disabled = False
        else:
            self.file_set(None, None)
            self.disabled = True

    def clear(self):
        self.task = None
        self.update()

    def _unfocused_cb(self, entry):
        if self.task and not entry.text:
            self.task.note = None
        self.top_widget.tasks_list.update_selected()

    def _clicked_cb(self, entry):
        if self.task is None:
            return

        if self.file[0] is not None:
            return

        self.task.create_note_filename()
        self.update()
        self.focus = True


class InfoWin(elm.InnerWindow):
    def __init__(self, parent):
        elm.InnerWindow.__init__(self, parent)

        vbox = elm.Box(self)
        vbox.show()
        self.content = vbox

        title = elm.Label(self, scale=2.0, text='Edone %s' % VERSION)
        title.show()
        vbox.pack_end(title)

        en = elm.Entry(self, text=INFO, editable=False, scrollable=True,
                       size_hint_weight=EXPAND_BOTH, size_hint_align=FILL_BOTH)
        en.show()
        vbox.pack_end(en)

        sep = elm.Separator(self, horizontal=True)
        sep.show()
        vbox.pack_end(sep)

        close = elm.Button(self, text='Close')
        close.callback_clicked_add(lambda b: self.delete())
        close.show()
        vbox.pack_end(close)

        self.activate()
        
