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
import logging
import os
import subprocess
# ============= standard library imports ========================
import sys
import warnings

import traits.has_traits
from pyface.confirmation_dialog import confirm
from pyface.message_dialog import warning
from pyface.qt import QtGui, QtCore
from traits.etsconfig.api import ETSConfig
from traitsui.qt.table_editor import TableDelegate
from traitsui.qt.ui_panel import heading_text

from pychron.environment.util import set_application_home

# ============= local library imports  ==========================

traits.has_traits.CHECK_INTERFACES = 1

warnings.simplefilter("ignore")
logger = logging.getLogger()


# def set_stylesheet(path):
#     app = get_app_qt4()
#     app.setStyle('plastique')
#
#     if path is None:
#         import shutil
#
#         force = True
#         default_css = 'darkorange.css'
#         from pychron.paths import paths
#         path = paths.hidden_path(default_css)
#         if not os.path.isfile(path) or force:
#             shutil.copyfile(default_css, path)
#
#     with open(path, 'r') as rfile:
#         app.setStyleSheet(rfile.read())


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


from traitsui.qt.ui_base import BasePanel
from traitsui.menu import UndoButton, RevertButton, HelpButton
from traitsui.qt.ui_panel import panel, _size_hint_wrapper
from traitsui.undo import UndoHistory


class myQTabBar(QtGui.QTabBar):
    def wheelEvent(self, *args, **kwargs):
        pass


class myPanel(BasePanel):
    """PyQt user interface panel for Traits-based user interfaces.
    """

    def __init__(self, ui, parent, is_subpanel):
        """Initialise the object.
        """
        self.ui = ui
        history = ui.history
        view = ui.view

        # Reset any existing history listeners.
        if history is not None:
            history.on_trait_change(self._on_undoable, 'undoable', remove=True)
            history.on_trait_change(self._on_redoable, 'redoable', remove=True)
            history.on_trait_change(self._on_revertable, 'undoable',
                                    remove=True)

        # Determine if we need any buttons or an 'undo' history.
        buttons = [self.coerce_button(button) for button in view.buttons]
        nr_buttons = len(buttons)
        has_buttons = (not is_subpanel and (nr_buttons != 1 or
                                            not self.is_button(buttons[0], '')))

        if nr_buttons == 0:
            if view.undo:
                self.check_button(buttons, UndoButton)
            if view.revert:
                self.check_button(buttons, RevertButton)
            if view.help:
                self.check_button(buttons, HelpButton)

        if not is_subpanel and history is None:
            for button in buttons:
                if self.is_button(button, 'Undo') or self.is_button(button, 'Revert'):
                    history = ui.history = UndoHistory()
                    break

        # Create the panel.
        self.control = panel(ui)
        # if self.control.isinstance(QtGui.QTabWidget):
        #     self.control.setTabBar(myQTabBar())

        # Suppress the title if this is a subpanel or if we think it should be
        # superceded by the title of an "outer" widget (eg. a dock widget).
        title = view.title
        if (is_subpanel or (isinstance(parent, QtGui.QMainWindow) and
                            not isinstance(parent.parent(), QtGui.QDialog)) or
                isinstance(parent, QtGui.QTabWidget)):
            title = ""

        # ============ Monkey Patch ===============
        if isinstance(parent, QtGui.QTabWidget):
            bar = parent.tabBar()
            if not isinstance(bar, myQTabBar):
                parent.setTabBar(myQTabBar())
        # =========================================

        # Panels must be widgets as it is only the TraitsUI PyQt code that can
        # handle them being layouts as well.  Therefore create a widget if the
        # panel is not a widget or if we need a title or buttons.
        if not isinstance(self.control, QtGui.QWidget) or title != "" or has_buttons:
            w = QtGui.QWidget()
            layout = QtGui.QVBoxLayout(w)
            layout.setContentsMargins(0, 0, 0, 0)

            # Handle any view title.
            if title != "":
                layout.addWidget(heading_text(None, text=view.title).control)

            if isinstance(self.control, QtGui.QWidget):
                layout.addWidget(self.control)
            elif isinstance(self.control, QtGui.QLayout):
                layout.addLayout(self.control)

            self.control = w

            # Add any buttons.
            if has_buttons:

                # Add the horizontal separator
                separator = QtGui.QFrame()
                separator.setFrameStyle(QtGui.QFrame.Sunken |
                                        QtGui.QFrame.HLine)
                separator.setFixedHeight(2)
                layout.addWidget(separator)

                # Add the special function buttons
                bbox = QtGui.QDialogButtonBox(QtCore.Qt.Horizontal)
                for button in buttons:
                    role = QtGui.QDialogButtonBox.ActionRole
                    if self.is_button(button, 'Undo'):
                        self.undo = self.add_button(button, bbox, role,
                                                    self._on_undo, False,
                                                    'Undo')
                        self.redo = self.add_button(button, bbox, role,
                                                    self._on_redo, False,
                                                    'Redo')
                        history.on_trait_change(self._on_undoable, 'undoable',
                                                dispatch='ui')
                        history.on_trait_change(self._on_redoable, 'redoable',
                                                dispatch='ui')
                    elif self.is_button(button, 'Revert'):
                        role = QtGui.QDialogButtonBox.ResetRole
                        self.revert = self.add_button(button, bbox, role,
                                                      self._on_revert, False)
                        history.on_trait_change(self._on_revertable, 'undoable',
                                                dispatch='ui')
                    elif self.is_button(button, 'Help'):
                        role = QtGui.QDialogButtonBox.HelpRole
                        self.add_button(button, bbox, role, self._on_help)
                    elif not self.is_button(button, ''):
                        self.add_button(button, bbox, role)
                layout.addWidget(bbox)

        # Ensure the control has a size hint reflecting the View specification.
        # Yes, this is a hack, but it's too late to repair this convoluted
        # control building process, so we do what we have to...
        self.control.sizeHint = _size_hint_wrapper(self.control.sizeHint, ui)


def monkey_patch_panel():
    from traitsui.qt import ui_panel
    ui_panel._Panel = myPanel


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

    from traitsui.qt.extra import checkbox_renderer

    checkbox_renderer.CheckboxRenderer = CheckboxRenderer


def monkey_patch_table_view():
    from traitsui.qt.table_editor import TableView

    def sizeHint(self):
        size_hint = QtGui.QTableView.sizeHint(self)

        # This method is sometimes called by Qt after the editor has been
        # disposed but before this control has been deleted:
        if self._editor.factory is None:
            return size_hint

        try:
            width = self.style().pixelMetric(
                QtGui.QStyle.PixelMetric.PM_ScrollBarExtent, QtGui.QStyleOptionHeader(), self
            )
        except AttributeError:
            width = 100

        for column in range(len(self._editor.columns)):
            width += self.sizeHintForColumn(column)

        size_hint.setWidth(int(width))
        return size_hint

    def resizeColumnsToContents(self):
        """Support proportional column width specifications."""

        # TODO: The proportional size specification approach found in the
        # TableColumns is not entirely compatible with the ability to
        # specify the resize_mode.  Namely, there are combinations of
        # specifications that are redundant, and others which are
        # contradictory.  Rework this method so that the various values
        # for **width** have a well-defined, sensible meaning for each
        # of the possible values of resize_mode.

        editor = self._editor
        available_space = self.viewport().width()
        hheader = self.horizontalHeader()

        # Compute sizes for columns with absolute or no size requests
        proportional = []
        for column_index in range(len(editor.columns)):
            column = editor.columns[column_index]
            requested_width = column.get_width()
            if (
                    column.resize_mode in ("interactive", "stretch")
                    and 0 < requested_width <= 1.0
            ):
                proportional.append((column_index, requested_width))
            elif (
                    column.resize_mode == "interactive"
                    and requested_width < 0
                    and self._initial_size
            ):
                # Keep previous size if initial sizing has been done
                available_space -= hheader.sectionSize(column_index)
            else:
                base_width = hheader.sectionSizeHint(column_index)
                width = int(max(base_width, self.sizeHintForColumn(column_index)))
                hheader.resizeSection(column_index, width)
                available_space -= width

        # Now use the remaining space for columns with proportional width
        # requests
        for column_index, percent in proportional:
            base_width = hheader.sectionSizeHint(column_index)
            width = int(max(base_width, int(percent * available_space)))
            hheader.resizeSection(column_index, width)

    TableView.resizeColumnsToContents = resizeColumnsToContents
    TableView.sizeHint = sizeHint

def monkey_patch_application_window():
    # see
    def _update_tool_bar_managers(obj, event):
        if obj.control is not None:
            # Remove the old toolbars.
            for child in obj.control.children():
                if isinstance(child, QtGui.QToolBar):
                    obj.control.removeToolBar(child)
                    child.deleteLater()

            # Add the new toolbars.
            if event.new is not None:
                #self._create_status_bar(self.control)
                obj._create_tool_bar(obj.control)

    from pyface.application_window import ApplicationWindow
    from traits.api import observe
    ApplicationWindow._update_tool_bar_managers = observe("tool_bar_managers.items")(_update_tool_bar_managers)


KLASS_MAP = {'pyexperiment': 'PyExperiment',
             'pyview': 'PyView',
             'pyvalve': 'PyValve',
             'pyco2': 'PyCO2',
             'pydiode': 'PyDiode',
             'pysampleprep': 'PySamplePrep',
             'pycrunch': 'PyCrunch'}


def entry_point(appname, debug=False):
    """
        entry point
    """
    klass = KLASS_MAP.get(appname)

    monkey_patch_preferences()
    monkey_patch_checkbox_render()
    monkey_patch_panel()
    monkey_patch_table_view()
    monkey_patch_application_window()

    # set_stylesheet('darkorange.css')
    env = initialize_version(appname, debug)
    if env:
        # set_stylesheet(None)

        if debug:
            set_commandline_args()

        # import app klass and pass to launch function
        if check_dependencies(debug):
            mod = __import__('pychron.applications.{}'.format(appname), fromlist=[klass])
            app = getattr(mod, klass)
            from pychron.envisage.pychron_run import launch

            launch(app)
    else:
        logger.critical('Failed to initialize environment')


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

    # from pychron.environment.util import get_environment
    # env = get_environment(appname)
    from pychron.envisage.user_login import get_user
    args = get_user()
    if args is None:
        return False
    else:
        user, env = args

    if not env:
        return False

    set_application_home(appname, env)

    from pychron.paths import paths
    logger.debug('using Pychron environment: {}'.format(env))
    paths.build(env)

    from configparser import ConfigParser, NoSectionError
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
    build_globals(user, debug)

    from pychron.core.helpers.logger_setup import logging_setup
    from pychron.paths import build_directories

    # build directories
    build_directories()
    paths.write_defaults()

    # setup logging. set a basename for log files and logging level

    from pychron.core.helpers.exception_helper import set_exception_handler
    set_exception_handler()

    try:
        logging_setup('pychron', level='DEBUG')
    except PermissionError as e:
        warning(None, 'Failed to setup logging due to a PermissionError. '
                      'Is Pychron already open? Please quit any running instance of Pychron '
                      'before trying to relaunch.  Error: {}'.format(e))
        return False
    except FileExistsError as e:
        warning(None, 'Failed to setup logging. '
                      ' Error: {}'.format(e))

        return False
    except FileExistsError as e:
        emsg = str(e)
        path = emsg.split('File exists:')[-1]
        warning(None, """Failed to setup logging.  Error: {}\n\n
Delete directory {} to proceed""".format(e, path))
        return False

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
                print(os.path.join(root, egg_name))


def build_globals(user, debug):
    try:
        from pychron.envisage.initialization.initialization_parser import InitializationParser
    except ImportError as e:
        from pyface.message_dialog import warning

        warning(None, str(e))

    ip = InitializationParser()

    err = ip.verify()
    if err:
        from pyface.message_dialog import warning
        warning(None, 'There is an issue with your initialization.xml file. Please resolve before relaunching\n'
                      '\n{}\n\nError: {}'.format(ip.path, err))
        sys.exit(1)

    from pychron.globals import globalv
    try:
        globalv.build(ip)
    except BaseException:
        from pyface.message_dialog import warning
        warning(None, 'There is an issue with your initialization.xml file. Please resolve before relaunching\n'
                      '\n{}'.format(ip.path))
        sys.exit(1)

    globalv.debug = debug
    globalv.username = user
# ============= EOF =============================================
