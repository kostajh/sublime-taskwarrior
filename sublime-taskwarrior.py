import sublime
import sublime_plugin
from taskw import TaskWarrior
import subprocess

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
                self.pri.append(['  ' + twproject])
        except:
            pass

        if twproject is not None or resetTasks == True:
            self.get_tasks(self.quick_panel_project_selected_index)
            return

        self.window.show_quick_panel(self.pri, self.get_tasks, sublime.MONOSPACE_FONT)

    # Get list of projects with pending tasks.
    def get_projects(self):
        # This will get an updated project list. Surely there is a better way.
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
        self.ti.append('  ' + twproject)
        self.ti.append([u'\u21b5' + ' Back to Projects'])
        self.ti.append([u'\u271A' + ' Add a Task'])

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
                if 'project' in task and twproject != "View all tasks":
                    if (task[u'project'] == twproject):
                        self.ti.append(['    ' + task[u'description']])
                else:
                    if twproject == "View all tasks":
                        self.ti.append(['    ' + task[u'description']])
        except:
            pass

        self.window.show_quick_panel(self.ti, self.get_mod_task_options, sublime.MONOSPACE_FONT)

    def get_mod_task_options(self, idx):

        global twtask

        if (idx == -1 or idx == 0):
            return

        # Go back
        if idx == 1:
            self.window.show_quick_panel(self.pri, self.get_tasks, sublime.MONOSPACE_FONT)
            return

        # Add task from input
        if idx == 2:
            self.window.run_command('taskwarrior_add_task_from_input')
            return

        twtask = twtasks[idx - 3]
        self.tasktitle = twtask[u'description']
        self.mod_options = [self.tasktitle, u'\u21b5' + ' Back to Tasks', u'\u2714' + ' Done', u'\u270E' + ' Modify', u'\u270E' + ' Annotate', u'\u2715' + ' Delete']

        self.window.show_quick_panel(self.mod_options, self.mod_task, sublime.MONOSPACE_FONT)

    def mod_task(self, idx):

        global twproject
        global twtask

        if idx == -1:
            return

        # Go Back
        if idx == 1:
            self.window.show_quick_panel(self.ti, self.get_mod_task_options, sublime.MONOSPACE_FONT)

        # Mark Task as done
        if idx == 2:
            # @todo use Taskw
            subprocess.call(['task', twtask[u'uuid'], 'done'])
            self.get_tasks(self.quick_panel_project_selected_index)

        # Modify Task
        if idx == 3:
            self.window.run_command('taskwarrior_modify_task_from_input')

        # Annotate Task
        if idx == 4:
            self.window.run_command('taskwarrior_annotate_task_from_input')

        # Delete Task
        if idx == 5:
            # @todo use Taskw
            # @todo add confirmation
            subprocess.call('yes | task ' + twtask[u'uuid'] + ' delete', shell=True)
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
            self.window.run_command('taskwarrior_view_tasks', {'resetTasks': True})
        pass
