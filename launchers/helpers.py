# ===============================================================================
# Copyright 2012 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
# ============= enthought library imports =======================
from traits.etsconfig.api import ETSConfig

from pychron.environment.util import set_application_home

ETSConfig.toolkit = "qt4"

from ConfigParser import NoSectionError

from pyface.confirmation_dialog import confirm
from pyface.constant import OK
from pyface.message_dialog import information, warning

from traitsui.qt4.table_editor import TableDelegate
from traitsui.qt4.extra import checkbox_renderer
from pyface.qt import QtGui, QtCore
import traits.has_traits
# ============= standard library imports ========================
import sys
import logging
import subprocess
import warnings
import os
# ============= local library imports  ==========================

traits.has_traits.CHECK_INTERFACES = 1

warnings.simplefilter("ignore")
logger = logging.getLogger()


def monkey_patch_preferences():
    def setfunc(obj, key, value):
        if isinstance(value, QtGui.QColor):
            value = '#{:02X}{:02X}{:02X}'.format(value.red(), value.green(), value.blue())
        else:
            value = str(value)

        obj._lk.acquire()
        old = obj._preferences.get(key)
        obj._preferences[key] = value

        # If the value is unchanged then don't call the listeners!
        if old == value:
            listeners = []

        else:
            listeners = obj._preferences_listeners[:]
        obj._lk.release()

        for listener in listeners:
            listener(obj, key, old, value)

    from apptools.preferences.preferences import Preferences
    Preferences._set = setfunc


def monkey_patch_checkbox_render():
    class CheckboxRenderer(TableDelegate):
        """ A renderer which displays a checked-box for a True value and an
            unchecked box for a false value.
        """

        # ---------------------------------------------------------------------------
        #  QAbstractItemDelegate interface
        # ---------------------------------------------------------------------------

        def editorEvent(self, event, model, option, index):
            """ Reimplemented to handle mouse button clicks.
            """
            if event.type() == QtCore.QEvent.MouseButtonRelease and event.button() == QtCore.Qt.LeftButton:
                column = index.model()._editor.columns[index.column()]
                obj = index.data(QtCore.Qt.UserRole)
                checked = bool(column.get_raw_value(obj))
                column.set_value(obj, not checked)
                return True
            else:
                return False

        def paint(self, painter, option, index):
            """ Reimplemented to paint the checkbox.
            """
            # Determine whether the checkbox is check or unchecked
            column = index.model()._editor.columns[index.column()]
            obj = index.data(QtCore.Qt.UserRole)
            checked = column.get_raw_value(obj)

            # First draw the background
            painter.save()
            row_brushes = [option.palette.base(), option.palette.alternateBase()]
            if option.state & QtGui.QStyle.State_Selected:
                bg_brush = option.palette.highlight()
            else:
                bg_brush = index.data(QtCore.Qt.BackgroundRole)
                if bg_brush == NotImplemented or bg_brush is None:
                    if index.model()._editor.factory.alternate_bg_color:
                        bg_brush = row_brushes[index.row() % 2]
                    else:
                        bg_brush = row_brushes[0]
            painter.fillRect(option.rect, bg_brush)

            # Then draw the checkbox
            style = QtGui.QApplication.instance().style()
            box = QtGui.QStyleOptionButton()
            box.palette = option.palette

            # Align the checkbox appropriately.
            box.rect = option.rect
            size = style.sizeFromContents(QtGui.QStyle.CT_CheckBox, box,
                                          QtCore.QSize(), None)
            box.rect.setWidth(size.width())
            margin = style.pixelMetric(QtGui.QStyle.PM_ButtonMargin, box)
            alignment = column.horizontal_alignment
            if alignment == 'left':
                box.rect.setLeft(option.rect.left() + margin)
            elif alignment == 'right':
                box.rect.setLeft(option.rect.right() - size.width() - margin)
            else:
                # FIXME: I don't know why I need the 2 pixels, but I do.
                box.rect.setLeft(option.rect.left() + option.rect.width() // 2 -
                                 size.width() // 2 + margin - 2)

            box.state = QtGui.QStyle.State_Enabled | QtGui.QStyle.State_Active
            if checked:
                box.state |= QtGui.QStyle.State_On
            else:
                box.state |= QtGui.QStyle.State_Off
            style.drawControl(QtGui.QStyle.CE_CheckBox, box, painter)
            painter.restore()

        def sizeHint(self, option, index):
            """ Reimplemented to provide size hint based on a checkbox
            """
            box = QtGui.QStyleOptionButton()
            style = QtGui.QApplication.instance().style()
            return style.sizeFromContents(QtGui.QStyle.CT_CheckBox, box,
                                          QtCore.QSize(), None)

    checkbox_renderer.CheckboxRenderer = CheckboxRenderer


def entry_point(modname, klass, setup_version_id='', debug=False):
    """
        entry point
    """
    monkey_patch_preferences()
    monkey_patch_checkbox_render()

    env = initialize_version(modname, debug)
    if env:
        if debug:
            set_commandline_args()

        # import app klass and pass to launch function
        if check_dependencies(debug):
            mod = __import__('pychron.applications.{}'.format(modname), fromlist=[klass])
            app = getattr(mod, klass)
            from pychron.envisage.pychron_run import launch

            launch(app, env)
    else:
        logger.critical('Failed to initialize user')


def check_dependencies(debug):
    """
        check the dependencies and install if possible/required
    """
    # suppress dependency checks temporarily
    return True

    with open('ENV.txt', 'r') as fp:
        env = fp.read().strip()

    ret = False
    logger.info('================ Checking Dependencies ================')
    for npkg, req in (('uncertainties', '2.1'),
                      ('pint', '0.5'),
                      # ('fant', '0.1')
                      ):
        try:
            pkg = __import__(npkg)
            ver = pkg.__version__
        except ImportError:
            if confirm(None, '"{}" is required. Attempt to automatically install?'.format(npkg)):
                if not install_package(pkg, env, debug):
                    warning(None, 'Failed installing "{}". Try to install manually'.format(npkg))
                    break

            else:
                warning(None, 'Install "{}" package. required version>={} '.format(npkg, req))
                break

        vargs = ver.split('.')
        maj = int(vargs[0])
        if maj < int(float(req)):
            warning(None, 'Update "{}" package. your version={}. required version>={} '.format(npkg, maj, req))
            break
        logger.info('{:<15s} >={:<5s} satisfied. Current ver: {}'.format(npkg, req, ver))
    else:
        ret = True

    logger.info('=======================================================')
    return ret


def install_package(pkg, env, debug):
    # this may not work when using conda environments
    # use absolute path to pip /anaconda/envs/.../bin/pip
    # use -n to specify environment

    if not subprocess.check_call(['conda', 'search', '{}'.format(pkg)], stdout=subprocess.PIPE):

        try:
            subprocess.check_call(['pip', 'install', '{}'.format(pkg)], stdout=subprocess.PIPE)
        except subprocess.CalledProcessError:
            return
    else:
        if debug:
            cmd = ['conda', 'install', '-yq', '{}'.format(pkg)]
        else:
            cmd = ['conda', 'install', '-yq', '-n', env, '{}'.format(pkg)]
        subprocess.check_call(cmd, stdout=subprocess.PIPE)

    if debug:
        cmd = ['conda', 'list']
    else:
        cmd = ['conda', 'list', '-n', env]

    deps = subprocess.check_output(cmd)
    for dep in deps.split('\n'):
        if dep.split(' ')[0] == pkg:
            logger.info('"{}" installed successfully'.format(pkg))
            return True


def set_commandline_args():
    from pychron.globals import globalv
    import argparse

    parser = argparse.ArgumentParser(description='Generate a password')
    parser.add_argument('-t', '--testbot',
                        action='store')
    args = parser.parse_args()
    globalv.use_testbot = args.testbot


def initialize_version(appname, debug):
    root = os.path.dirname(__file__)

    if not debug:
        add_eggs(root)
    else:
        build_sys_path()

    from pychron.environment.util import get_environment
    env = get_environment(appname)
    if not env:
        logger.info('no environment available')
        from pyface.directory_dialog import DirectoryDialog

        information(None, 'An "environment" directory is not set in Preferences/General. Please select a valid '
                          'directory')
        dlg = DirectoryDialog(action='open', default_directory=os.path.expanduser('~'))
        result = dlg.open()
        if result == OK:
            env = str(dlg.path)
            from pychron.environment.util import set_environment
            set_environment(env, appname)
    else:
        set_application_home(env)

    if not env:
        return False

    from pychron.paths import paths
    logger.debug('using Pychron environment: {}'.format(env))
    paths.build(env)

    from ConfigParser import ConfigParser
    cp = ConfigParser()
    pref_path = os.path.join(ETSConfig.application_home, 'preferences.ini')
    cp.read(pref_path)
    try:
        cp.set('pychron.general', 'environment', env)
    except NoSectionError:
        cp.add_section('pychron.general')
        cp.set('pychron.general', 'environment', env)

    root = os.path.dirname(pref_path)
    if not os.path.isdir(root):
        os.mkdir(root)

    with open(pref_path, 'w') as wfile:
        cp.write(wfile)

    # build globals
    build_globals(debug)

    from pychron.core.helpers.logger_setup import logging_setup
    from pychron.paths import build_directories

    # build directories
    build_directories()
    paths.write_defaults()

    # setup logging. set a basename for log files and logging level
    logging_setup('pychron', level='DEBUG')

    from pychron.core.helpers.exception_helper import set_exception_handler, report_issues
    set_exception_handler()
    report_issues()

    return env


def build_sys_path():
    """
        need to launch from terminal
    """

    sys.path.insert(0, os.path.dirname(os.getcwd()))


def add_eggs(root):
    egg_path = os.path.join(root, 'pychron.pth')
    if os.path.isfile(egg_path):
        # use a pychron.pth to get additional egg paths
        with open(egg_path, 'r') as rfile:
            eggs = [ei.strip() for ei in rfile.read().split('\n')]
            eggs = [ei for ei in eggs if ei]

            for egg_name in eggs:
                # sys.path.insert(0, os.path.join(root, egg_name))
                sys.path.append(os.path.join(root, egg_name))
                print os.path.join(root, egg_name)


def build_globals(debug):
    try:
        from pychron.envisage.initialization.initialization_parser import InitializationParser
    except ImportError, e:
        from pyface.message_dialog import warning

        warning(None, str(e))

    ip = InitializationParser()

    from pychron.globals import globalv

    globalv.build(ip)
    globalv.debug = debug

# ============= EOF =============================================
