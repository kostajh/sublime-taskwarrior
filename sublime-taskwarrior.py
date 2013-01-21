import sublime
import sublime_plugin
from taskw import TaskWarrior
import subprocess
import datetime

twprojects = None
twproject = None
twtasks = None
twtask = None
twconf = None

settings = sublime.load_settings("sublime-taskwarrior.sublime-settings")


class TaskwarriorViewTasksCommand (sublime_plugin.WindowCommand):

    quick_panel_project_selected_index = None

    def get_conf(self):

        global twconf
        w = TaskWarrior()
        twconf = w.load_config()
        return

    def run(self, resetProjects=False, resetTasks=False):

        global twprojects
        global twproject

        # Get configuration if needed.
        if twconf == None:
            self.get_conf()

        if twprojects is None or resetProjects == True:
            twprojects = self.get_projects()

        self.pri = []
        self.pri.append([u'\u271A' + ' Add a New Task'])
        try:
            for twproject in twprojects:
                # @todo Display task counts for project
                # `task project:proposals count status:pending`
                self.pri.append(['  ' + twproject])
        except:
            pass

        if twproject is not None or resetTasks == True:
            self.get_tasks(self.quick_panel_project_selected_index)
            return
        self.window.show_quick_panel(self.pri, self.get_tasks, sublime.MONOSPACE_FONT)

    # Get list of projects with pending tasks.
    def get_projects(self):
        # Calling 'task' will get an updated project list.
        subprocess.call(['task'])
        twprojects = []
        twprojects.append('View all tasks')
        w = TaskWarrior()
        tasks = w.load_tasks()
        twtasks = tasks['pending']
        for task in twtasks:
            if 'project' in task:
                if task[u'project'] not in twprojects:
                    twprojects.append(task[u'project'])
        return twprojects

    # Get pending tasks.
    def get_tasks(self, idx):
        # This will get an updated task list. Surely there is a better way.
        subprocess.call(['task'])
        global twproject
        global twtasks

        if idx == -1:
            return

        self.quick_panel_project_selected_index = idx

        # check this.
        if idx is None:
            idx = 1

        twproject = twprojects[idx - 1]

        self.ti = []
        self.ti.append([u'\u21b5' + ' Back to Projects', 'View list of projects with pending tasks'])
        self.ti.append([u'\u271A' + ' Add a Task', 'Add a new task'])

        # Build list of pending tasks for selected project.
        w = TaskWarrior()
        tasks = w.load_tasks()
        pending_tasks = tasks['pending']
        twtasks = []
        for task in pending_tasks:
            if 'project' in task and twproject != "View all tasks":
                if task[u'project'] == twproject:
                    twtasks.append(task)
            else:
                if twproject == "View all tasks":
                    twtasks.append(task)

        try:
            for task in twtasks:
                meta_data = ''
                due = ''
                tags = ''
                priority = ''
                created = "Created: " + datetime.datetime.fromtimestamp(int(task[u'entry'])).strftime('%m-%d-%y')
                if 'due' in task:
                    due = "Due: " + datetime.datetime.fromtimestamp(int(task[u'due'])).strftime('%m-%d-%y')
                if 'tags' in task:
                    tags = "Tags: " + ', '.join(task[u'tags'])
                if 'priority' in task:
                    priority = task[u'priority']
                if priority != '':
                    meta_data += priority + " "
                if due != '':
                    meta_data += due + " "
                if tags != '':
                    meta_data += tags + " "
                if 'project' in task and twproject != "View all tasks":
                    if (task[u'project'] == twproject):
                        meta_data += created + " "
                        self.ti.append([task[u'description'], meta_data])
                else:
                    if twproject == "View all tasks":
                        if 'project' in task:
                            meta_data += "@" + task[u'project'] + " " + created
                        self.ti.append([task[u'description'], meta_data])
        except:
            pass

        self.window.show_quick_panel(self.ti, self.get_mod_task_options, sublime.MONOSPACE_FONT)

    def get_mod_task_options(self, idx):

        global twtask

        if (idx == -1):
            return

        # Go back
        if idx == 0:
            self.window.show_quick_panel(self.pri, self.get_tasks, sublime.MONOSPACE_FONT)
            return

        # Add task from input
        if idx == 1:
            self.window.run_command('taskwarrior_add_task_from_input')
            return

        twtask = twtasks[idx - 2]
        self.tasktitle = twtask[u'description']
        status = u'\u270E' + ' Start task'
        if 'start' in twtask:
            status = u'\u2715' + ' Stop task'

        self.mod_options = [self.tasktitle, u'\u21b5' + ' Back to Tasks', status, u'\u2714' + ' Done', u'\u270E' + ' Modify', u'\u270E' + ' Annotate', u'\u2715' + ' Delete']

        self.window.show_quick_panel(self.mod_options, self.mod_task, sublime.MONOSPACE_FONT)

    def mod_task(self, idx):

        global twproject
        global twtask

        if idx == -1:
            return

        # Go Back
        if idx == 1:
            self.window.show_quick_panel(self.ti, self.get_mod_task_options, sublime.MONOSPACE_FONT)

        # Start or stop task
        if idx == 2:
            status_command = 'start'
            status_command_msg = 'Started task '
            if 'start' in twtask:
                status_command = 'stop'
                status_command_msg = 'Stopped task '
            subprocess.call(['task', twtask[u'uuid'], status_command])
            sublime.status_message(status_command_msg + '"' + twtask[u'description'] + '"')
            self.get_tasks(self.quick_panel_project_selected_index)

        # Mark Task as done
        if idx == 3:
            # @todo use Taskw
            subprocess.call(['task', twtask[u'uuid'], 'done'])
            self.get_tasks(self.quick_panel_project_selected_index)

        # Modify Task
        if idx == 4:
            self.window.run_command('taskwarrior_modify_task_from_input')

        # Annotate Task
        if idx == 5:
            self.window.run_command('taskwarrior_annotate_task_from_input')

        # Delete Task
        if idx == 6:
            # @todo use Taskw
            # @todo add confirmation
            subprocess.call('yes | task ' + twtask[u'uuid'] + ' delete', shell=True)
            sublime.status_message('Deleted task "' + twtask[u'description'] + '"')
            self.get_tasks(self.quick_panel_project_selected_index)


class TaskwarriorAddTaskFromInputCommand(sublime_plugin.WindowCommand):

    global twproject

    def run(self):
        self.task = {'title': ''}
        self.window.show_input_panel('Add a Task:', '', self.on_done, None, None)
        pass

    def on_done(self, input):
        if input != '':
            self.task['title'] = input
            subprocess.call(['task', 'add', input])
            sublime.status_message('Added task "' + input + '"')
            self.window.run_command('taskwarrior_view_tasks', {'resetTasks': True})
        pass


class TaskwarriorAnnotateTaskFromInputCommand(sublime_plugin.WindowCommand):

    global twtask

    def run(self):
        self.window.show_input_panel('Annotate "' + twtask[u'description'] + '"', sublime.get_clipboard(), self.on_done, None, None)
        pass

    def on_done(self, input):
        if input != '':
            subprocess.call(['task', twtask[u'uuid'], 'annotate', input])
            sublime.status_message('Annotated task "' + twtask[u'description'] + '"')
            self.window.run_command('taskwarrior_view_tasks', {'resetTasks': True})
        pass


class TaskwarriorModifyTaskFromInputCommand(sublime_plugin.WindowCommand):

    global twtask

    def run(self):
        self.window.show_input_panel('Modify Task:', twtask[u'description'], self.on_done, None, None)
        pass

    def on_done(self, input):
        if input != '':
            twtask[u'description'] = input
            subprocess.call(['task', twtask[u'uuid'], 'mod', input])
            sublime.status_message('Modified task "' + twtask[u'description'] + '"')
            self.window.run_command('taskwarrior_view_tasks', {'resetTasks': True})
        pass


class TaskwarriorAnnotateNewestTaskFromClipboardCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        w = TaskWarrior()
        tasks = w.load_tasks()
        pending_tasks = tasks[u'pending']
        twtask = pending_tasks[-1]
        clipboard = sublime.get_clipboard()
        if clipboard != '' and twtask[u'uuid'] != '':
            subprocess.call(['task', twtask[u'uuid'], 'annotate', clipboard])
            sublime.status_message('Annotated task "' + twtask[u'description'] + '" with text "' + clipboard + '"')
        pass
