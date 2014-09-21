# ===============================================================================
# Copyright 2014 Jake Ross
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
from traits.api import Str, Bool, Int, File, Event
from traitsui.api import View, Group
#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.directory_editor import CustomEditor
from traitsui.qt4.file_editor import _TreeView, filter_trait
from pyface.qt import QtCore, QtGui


class _myTreeView(_TreeView):
    def __init__(self, editor):
        super(_TreeView, self).__init__()
        self.doubleClicked.connect(editor._on_dclick)
        self.clicked.connect(editor._on_select)
        self._editor = editor


class _DirectoryEditor(CustomEditor):
    selected = Event

    def init( self, parent ):
        self.control = _myTreeView(self)

        self._model = model = QtGui.QFileSystemModel()
        self.control.setModel(model)

        # Don't apply filters to directories and don't show "." and ".."
        model.setFilter(QtCore.QDir.AllDirs | QtCore.QDir.Files |
                        QtCore.QDir.Drives | QtCore.QDir.NoDotAndDotDot)

        # Hide filtered out files instead of only disabling them
        self._model.setNameFilterDisables(False)

        # Show the full filesystem by default.
        model.setRootPath(QtCore.QDir.rootPath())

        # Hide the labels at the top and only show the column for the file name
        self.control.header().hide()
        for column in xrange(1, model.columnCount()):
            self.control.hideColumn(column)

        factory = self.factory
        self.filter = factory.filter
        self.root_path = factory.root_path
        self.sync_value(factory.filter_name, 'filter', 'from', is_list=True)
        self.sync_value(factory.root_path_name, 'root_path', 'from')
        self.sync_value(factory.reload_name, 'reload', 'from')
        self.sync_value(factory.dclick_name, 'dclick', 'to')
        self.sync_value(factory.selected_name, 'selected', 'to')

        self.set_tooltip()

        # This is needed to enable horizontal scrollbar.
        self.control.header().setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
        self.control.header().setStretchLastSection(False)

    def _on_select(self, idx):
        self.selected = unicode(self._model.filePath(idx))


class myDirectoryEditor(BasicEditorFactory):
    klass = _DirectoryEditor
    filter = filter_trait

    # Optional extended trait name of the trait containing the list of filters:
    filter_name = Str

    # Should file extension be truncated?
    truncate_ext = Bool( False )

    # Can the user select directories as well as files?
    allow_dir = Bool( False )

    # Is user input set on every keystroke? (Overrides the default) ('simple'
    # style only):
    auto_set = False

    # Is user input set when the Enter key is pressed? (Overrides the default)
    # ('simple' style only):
    enter_set = True

    # The number of history entries to maintain:
    entries = Int( 10 )

    # The root path of the file tree view ('custom' style only, not supported
    # under wx). If not specified, the filesystem root is used.
    root_path = File

    # Optional extend trait name of the trait containing the root path.
    root_path_name = Str

    # Optional extended trait name used to notify the editor when the file
    # system view should be reloaded ('custom' style only):
    reload_name = Str

    # Optional extended trait name used to notify when the user double-clicks
    # an entry in the file tree view. The associated path is assigned it:
    dclick_name = Str

    selected_name = Str
    # The style of file dialog to use when the 'Browse...' button is clicked
    # Should be one of 'open' or 'save'
    dialog_style = Str('open')

    #---------------------------------------------------------------------------
    #  Traits view definition:
    #---------------------------------------------------------------------------

    traits_view = View( [ [ '<options>',
                        'truncate_ext{Automatically truncate file extension?}',
                        '|options:[Options]>' ],
                          [ 'filter', '|[Wildcard filters]<>' ] ] )

    extras = Group()

#============= EOF =============================================



