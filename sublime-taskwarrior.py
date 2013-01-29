import sublime
import sublime_plugin
import subprocess
import datetime
import json

twprojects = None
twproject = None
twtasks = None
twtask = None

settings = sublime.load_settings("sublime-taskwarrior.sublime-settings")


class TaskWarriorAPI:
    def load_tasks(self):
        tasks = dict()
        task_data = subprocess.Popen(['task', 'rc.json.array=TRUE', 'export', 'status:pending'], stdout=subprocess.PIPE).communicate()[0]
        tasks = json.loads(task_data)
        return tasks

    def task_add(self, input):
        subprocess.call(['task', 'add', input])
        tasks = self.load_tasks()
        return tasks[-1]['id']

    def task_annotate(self, uuid, input):
        subprocess.call(['task', uuid, 'annotate', input])
        return

    def task_modify(self, uuid, input):
        subprocess.call(['task', uuid, 'mod', input])
        return

    def task_done(self, uuid):
        subprocess.call(['task', uuid, 'done'])
        return

    def task_status(self, uuid, status):
        subprocess.call(['task', uuid, status])
        return

    def task_view(self, uuid):
        task_info = subprocess.Popen(['task', uuid], stdout=subprocess.PIPE).communicate()[0]
        return task_info


class TaskwarriorViewTasksCommand (sublime_plugin.WindowCommand):

    quick_panel_project_selected_index = None

    def run(self, resetProjects=False, resetTasks=False):

        global twprojects
        global twproject
        tw = TaskWarriorAPI()

        if twprojects is None or resetProjects == True:
            twprojects = self.get_projects()

        self.pri = []
        self.pri.append([u'\u271A' + ' Add a New Task', 'Create a task from the input panel'])
        try:
            tw.load_tasks()
            for twproject in twprojects:
                additional_data = 'See a list of all pending tasks'
                if twproject != 'View all tasks':
                    pending = 'Pending: ' + subprocess.Popen(['task', 'project:' + twproject, 'count', 'status:pending'], stdout=subprocess.PIPE).communicate()[0]
                    completed = 'Completed: ' + subprocess.Popen(['task', 'project:' + twproject, 'count', 'status:completed'], stdout=subprocess.PIPE).communicate()[0]
                    additional_data = pending + completed
                self.pri.append([twproject, additional_data])
        except:
            pass

        if twproject is not None or resetTasks == True:
            self.get_tasks(self.quick_panel_project_selected_index)
            return
        self.window.show_quick_panel(self.pri, self.get_tasks, sublime.MONOSPACE_FONT)

    # Get list of projects with pending tasks.
    def get_projects(self):
        # Calling 'task' will get an updated project list.
        tw = TaskWarriorAPI()
        tasks = tw.load_tasks()
        twprojects = []
        twprojects.append('View all tasks')
        for task in tasks:
            if 'project' in task:
                if task[u'project'] not in twprojects:
                    twprojects.append(task[u'project'])
        return twprojects

    # Get pending tasks.
    def get_tasks(self, idx):
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
        tw = TaskWarriorAPI()
        tasks = tw.load_tasks()
        twtasks = []
        for task in tasks:
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
                created = "Created: " + str(datetime.datetime.strptime(task[u'entry'], "%Y%m%dT%H%M%SZ"))
                if 'due' in task:
                    due = "Due: " + str(datetime.datetime.strptime(task[u'due'], "%Y%m%dT%H%M%SZ"))
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
        status = u'\u21AF' + ' Start task'
        if 'start' in twtask:
            status = u'\u21BA' + ' Stop task'

        self.mod_options = [self.tasktitle, u'\u21b5' + ' Back to Tasks', status, u'\u2714' + ' Done', u'\u2600' + ' View details', u'\u270E' + ' Modify', u'\u221E' + ' Annotate', u'\u2715' + ' Delete']

        self.window.show_quick_panel(self.mod_options, self.mod_task, sublime.MONOSPACE_FONT)

    def mod_task(self, idx):

        global twproject
        global twtask

        tw = TaskWarriorAPI()

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
            tw.task_status(twtask[u'uuid'], status_command)
            sublime.status_message(status_command_msg + '"' + twtask[u'description'] + '"')
            self.get_tasks(self.quick_panel_project_selected_index)

        # Mark Task as done
        if idx == 3:
            tw.task_done(twtask[u'uuid'])
            sublime.status_message('Completed task "' + twtask[u'description'] + '"')
            self.get_tasks(self.quick_panel_project_selected_index)

        # View details of a task
        if idx == 4:
            if not hasattr(self, 'output_view'):
                self.output_view = self.window.get_output_panel('task_view')
            v = self.output_view
            # Write task details to the output panel
            edit = v.begin_edit()
            v.insert(edit, v.size(), 'Details for task "' + twtask[u'description'] + '":' + '\n')
            task_info = tw.task_view(twtask[u'uuid'])
            v.insert(edit, v.size(), task_info)
            v.end_edit(edit)
            v.show(v.size())
            self.window.run_command("show_panel", {"panel": "output." + 'task_view'})

        # Modify Task
        if idx == 5:
            self.window.run_command('taskwarrior_modify_task_from_input')

        # Annotate Task
        if idx == 6:
            self.window.run_command('taskwarrior_annotate_task_from_input')

        # Delete Task
        if idx == 7:
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
            tw = TaskWarriorAPI()
            task_id = tw.task_add(input)
            if type(task_id) is int:
                sublime.status_message("Added task %s: %s" % (str(task_id), input))
            else:
                sublime.status_message("Failed to add task: %s" % input)
            self.window.run_command('taskwarrior_view_tasks', {'resetTasks': True})
        pass


class TaskwarriorAnnotateTaskFromInputCommand(sublime_plugin.WindowCommand):

    global twtask

    def run(self):
        self.window.show_input_panel('Annotate "' + twtask[u'description'] + '"', sublime.get_clipboard(), self.on_done, None, None)
        pass

    def on_done(self, input):
        if input != '':
            tw = TaskWarriorAPI()
            tw.task_annotate(twtask[u'uuid'], input)
            sublime.status_message('Annotated task "' + twtask[u'description'] + '"')
            self.window.run_command('taskwarrior_view_tasks', {'resetTasks': True})
        pass


class TaskwarriorAnnotateNewestTaskFromInputCommand(sublime_plugin.WindowCommand):

    def run(self):
        tw = TaskWarriorAPI()
        tasks = tw.load_tasks()
        self.twtask = tasks[-1]
        self.window.show_input_panel('Annotate "' + self.twtask[u'description'] + '"', "", self.on_done, None, None)
        pass

    def on_done(self, input):
        if input != '':
            tw = TaskWarriorAPI()
            tw.task_annotate(self.twtask[u'uuid'], input)
            sublime.status_message('Annotated task "' + self.twtask[u'description'] + '" with "' + input + '"')
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
            tw = TaskWarriorAPI()
            tw.task_modify(twtask[u'uuid'], input)
            sublime.status_message('Modified task "' + twtask[u'description'] + '"')
            self.window.run_command('taskwarrior_view_tasks', {'resetTasks': True})
        pass


class TaskwarriorAnnotateNewestTaskFromClipboardCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        tw = TaskWarriorAPI()
        tasks = tw.load_tasks()
        twtask = tasks[-1]
        clipboard = sublime.get_clipboard()
        if clipboard != '' and twtask[u'uuid'] != '':
            tw.annotate(twtask[u'uuid'], clipboard)
            sublime.status_message('Annotated task "' + twtask[u'description'] + '" with text "' + clipboard + '"')
        pass
