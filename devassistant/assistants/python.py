import os

import plumbum

from devassistant import argument
from devassistant import assistant_base
from devassistant import exceptions
from devassistant.logger import logger

from devassistant.command_helpers import PathHelper, RPMHelper, YUMHelper

class PythonAssistant(assistant_base.AssistantBase):
    def get_subassistants(self):
        return [DjangoAssistant, FlaskAssistant, LibAssistant]

    name = 'python'
    fullname = 'Python'
    description = 'This is base Python assistant, you have to choose a specific project type.'

    args = [argument.Argument('-e', '--eclipse',
                              required=False,
                              action='store_true',
                              help='Configure as eclipse project.')]

    def _eclipse_dep_list(self, **kwargs):
        return ['eclipse-pydev']

class DjangoAssistant(PythonAssistant):
    name = 'django'
    fullname = 'Django'
    description = 'Django assistant will help you create a basic Django project and install dependencies.'

    args = [argument.Argument('-n', '--name',
                              required=True,
                              help='Name of the project (can also be full or relative path)')] + \
           PythonAssistant.args

    usage_string_fmt = '{fullname} Assistant lets you create a Django project.'

    def errors(self, **kwargs):
        errors = []
        self.path = os.path.abspath(os.path.expanduser(kwargs['name']))

        path_exists = PathHelper.path_exists(self.path)
        if path_exists:
            errors.append('Path exists: {0}'.format(self.path))
        return errors

    def dependencies(self, **kwargs):
        deps = ['python-django']

        if kwargs.get('eclipse', None):
            deps.append('eclipse-pydev')

        self._install_dependencies(*deps, **kwargs)

    def run(self, **kwargs):
        django_admin = plumbum.local['django_admin']
        project_path, project_name = os.path.split(self.path)

        logger.info('Creating Django project {name} in {path}...'.format(path=project_path,
                                                                         name=project_name))
        PathHelper.mkdir_p(project_path)
        with plumbum.local.cwd(project_path):
            django_admin('startproject', project_name)
        self._dot_devassistant_create(self.path, **kwargs)
        logger.info('Django project {name} in {path} has been created.'.format(path=project_path,
                                                                               name=project_name))

class FlaskAssistant(PythonAssistant):
    name = 'flask'
    fullname = 'Flask'
    description = 'Flask assistant will help you create a basic Flask project and install dependencies.'

    args = [argument.Argument('-n', '--name',
                              required=True,
                              help='Name of the project (can also be full or relative path)')] + \
           PythonAssistant.args

    def errors(self, **kwargs):
        errors = []
        self.path = os.path.abspath(os.path.expanduser(kwargs['name']))

        path_exists = PathHelper.path_exists(self.path)
        if path_exists:
            errors.append('Path exists: {0}'.format(self.path))
        return errors

    def dependencies(self, **kwargs):
        # TODO: this should be substituted by a yum group
        deps = ['python-flask', 'python-flask-sqlalchemy', 'python-flask-wtf']
        if kwargs.get('eclipse', None):
            deps.append('eclipse-pydev')

        self._install_dependencies(*deps)

    def run(self, **kwargs):
        logger.info('Kickstarting a Flask project under {0}'.format(kwargs['name']))
        logger.info('Creating directory structure...')
        PathHelper.mkdir_p(self.path)
        PathHelper.mkdir_p('{0}/static'.format(self.path))
        PathHelper.mkdir_p('{0}/templates'.format(self.path))

        logger.info('Creating initial project files...')
        # the flask template doesn't in fact need rendering, so just copy it
        PathHelper.cp(os.path.join(self.template_dir, 'python', 'flask'),
                      os.path.join(self.path, '__init__.py'))
        self._dot_devassistant_create(self.path, **kwargs)

class LibAssistant(PythonAssistant):
    name = 'lib'
    fullname = 'Python Library'
    description = 'Lib assistant will help you create a custom library using setuptools.'

    args = [argument.Argument('-n', '--name',
                              required=True,
                              help='Name of the library (can also be full or relative path)')] + \
           PythonAssistant.args

    usage_string_fmt = '{fullname} Assistant lets you create a custom python library.'

    def errors(self, **kwargs):
        errors = []
        self.path = os.path.abspath(os.path.expanduser(kwargs['name']))

        path_exists = PathHelper.path_exists(self.path)
        if path_exists:
            errors.append('Path exists: {0}'.format(self.path))
        return errors

    def dependencies(self, **kwargs):
        deps = ['python-setuptools']
        if kwargs.get('eclipse', None):
            deps.append('eclipse-pydev')

        self._install_dependencies(*deps)

    def run(self, **kwargs):
        lib_path, lib_name = os.path.split(self.path)

        logger.info('Creating library project {name} in {path}...'.format(path=lib_path,
                                                                          name=lib_name))
        PathHelper.mkdir_p(self.path)
        with plumbum.local.cwd(self.path):
            PathHelper.mkdir_p(lib_name)
            touch = plumbum.local['touch']
            touch('{0}/__init__.py'.format(lib_name))
            setup_py = self._jinja_env.get_template(os.path.join('python', 'lib', 'setup.py'))
            with open('setup.py', 'w') as f:
                f.write(setup_py.render(name=lib_name))
        self._dot_devassistant_create(self.path, **kwargs)
        logger.info('Library project {name} in {path} has been created.'.format(path=lib_path,
                                                                               name=lib_name))
