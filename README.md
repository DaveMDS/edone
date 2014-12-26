
Edone
=====

A GTD (todo) application written in python-efl

## Features ##

* Todo.txt compliant
* Great view flexibility: sorting and grouping of tasks
* Customizable colors for +projects and @contexts
* Additional notes for tasks (custom tag note:XXX.txt)
* Additional completion progress for tasks (custom tag prog:XX)

## Todo ##
* ~~Fix fileselector when selected file not esists~~
* ~~Click on Menu should close the menu (if yet opened)~~
* Reload side lists when edited done
* ~~Safe window close (ask to save)~~
* ~~Remeber view button status (all,todo,done)~~
* ~~Sort by priority~~
* ~~Group by tags~~
* ~~Task deletion~~
* Start/Due dates
* ~~Tags colors~~
* ~~GUI way to edit tasks properties (todo/done, prio)~~
* ~~Edit tasks inplace`~~
* DND tags-on-tasks and tasks-on-tags
* ~~Notes for tasks~~
* Attachments for tasks
* ~~Task completion progress~~

## Requirements ##

* Python 2.7 or higher
* Python-EFL 1.13 or higher
* python modules: efl, xdg


## Installation ##

* For system-wide installation (needs administrator privileges):

 `(sudo) python setup.py install`

* For user installation:

 `python setup.py install --user`

* To install for different version of python:

 `pythonX setup.py install`

* Install with a custom prefix:

 `python setup.py install --prefix=/MY_PREFIX`

* To create distribution packages:

 `python setup.py sdist`


## License ##

GNU General Public License v3 - see COPYING
