# ===============================================================================
# Copyright 2013 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
"""
    the GeoEditor will not work in current setup

    cannot use gui elements from qgis in pychron
    pychron uses pyside, qgis uses pyqt4

"""
from pychron.core.ui import set_toolkit
set_toolkit('qt4')

from traits.api import HasTraits, Int
from traitsui.api import View, Item

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.qt4.basic_editor_factory import BasicEditorFactory
from traitsui.qt4.editor import Editor
from qgis.gui import QgsMapCanvas


class _GeoEditor(Editor):
    def init(self, parent):
        self.control=self._create_control(parent)

    def _create_control(self, parent):
        self._canvas_ctrl=QgsMapCanvas()
        return self._canvas_ctrl

    def update_editor(self):
        pass

class GeoEditor(BasicEditorFactory):
    klass=_GeoEditor



class A(HasTraits):
    a=Int
    def traits_view(self):
        v=View(Item('a', editor=GeoEditor()))
        return v

if __name__=='__main__':
    a=A()
    a.configure_traits()
# ============= EOF =============================================

