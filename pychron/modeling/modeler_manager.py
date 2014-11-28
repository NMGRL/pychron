# ===============================================================================
# Copyright 2011 Jake Ross
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

#============= enthought library imports =======================
from traits.api import Instance, DelegatesTo, List, Property
from traitsui.api import View, Item
#============= standard library imports ========================
# import os
#============= local library imports  ==========================
from modeler import Modeler
from pychron.envisage.core.envisage_manager import EnvisageManager
from pychron.envisage.core.envisage_editor import EnvisageEditor
from apptools.preferences.preference_binding import bind_preference

class MEditor(EnvisageEditor):
    '''
    '''
    id_name = 'Modeler'
    view_name = 'graph_view'

class ModelerManager(EnvisageManager):
    _modeler = Instance(Modeler)
    modeler = Property(depends_on='_modeler')
    modelers = List(Modeler)
    editor_klass = MEditor

    selected_datum = DelegatesTo('modeler', prefix='selected')

    _include_panels = None

    fortran_processes = DelegatesTo('modeler')
#    line_width = Int(1)
#    arrhenius_plot_type = Str('scatter')

    def _selected_changed(self, old, new):
        self._modeler = new

    def new_modeler(self):

        m = self._modeler_factory()

    #        if self.modeler:
#            m.logr_ro_line_width = self.modeler.logr_ro_line_width
#            m.arrhenius_plot_type = self.modeler.arrhenius_plot_type

#        if self._include_panels:
#            m.include_panels = self._include_panels

        info = m.edit_traits(view='configure_view')

        if info.result:
            # remember this modelers include panels for the future modelers
#            self._include_panels = m.include_panels


            m.refresh_graph()
            self.open_modeler(m=m)

    def _get_modeler(self):
        return self._modeler

    def parse_autoupdate(self):
        self.modeler.parse_autoupdate()

    def open_run_configuration(self):
        self.modeler.open_run_configuration()

    def run_model(self):
        self.modeler.run_model()

    def open_default(self):
        self.open_modeler()

    def open_modeler(self, m=None):
        if m is None:
            m = self.modeler
        self.selected = m
        self.window.workbench.edit(m,
                                   kind=self.editor_klass,
                                   use_existing=False
                                   )

        self._modeler = m

    def save(self):
        path = self._file_dialog('save as')
        if path is not None:
            self.modeler.graph.save_png(path=path)

    def __modeler_default(self):
        m = self._modeler_factory()
        m.refresh_graph()
        return m

    def _modeler_factory(self):
        m = Modeler(
#                    line_width=self.line_width,
#                    arrhenius_plot_type=self.arrhenius_plot_type
                    )
        bind_preference(m, 'logr_ro_line_width', 'pychron.mdd.logr_ro_line_width')
        bind_preference(m, 'arrhenius_plot_type', 'pychron.mdd.plot_type')
        bind_preference(m, 'clovera_directory', 'pychron.mdd.clovera_dir')
        bind_preference(m, 'data_directory', 'pychron.mdd.data_dir')

        return m

    def data_select_view(self):
        return View(Item('_modeler', style='custom', show_label=False))
#============= views ===================================
#============= EOF ====================================
