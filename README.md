# Sublime Taskwarrior

A plugin for ST2 to view, modify and add tasks with [Taskwarrior](http://www.taskwarrior.org).

When viewing tasks, tasks are organized by project as well as a "View all tasks" item. Select a task to complete, modify, or delete it.

When modifying or adding a task, use the same Taskwarrior syntax as you would on the command line.

## Commands

`super+alt+t` - View and modify tasks

`super+shift+a` - Add task

## Requirements

### Taskwarrior 2

This plugin will not work with Taskwarrior 1.x.

### taskw

[Taskw](https://github.com/ralphbean/taskw) is a python API for Taskwarrior.

If you don't have pip-2.6: `sudo easy_install-2.6 pip`

Then: `sudo pip-2.6 install taskw`

### System

This plugin has been tested on OSX 10.8. It should work on Linux and Windows, but if you test please let us know.

## Credits

Authored by [Kosta Harlan](http://kostaharlan.net)

Code borrows heavily from [Sublime Google Tasks](https://github.com/jpswelch/sublime-google-tasks)
