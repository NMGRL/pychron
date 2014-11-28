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
from traits.api import  on_trait_change
#============= standard library imports ========================

#============= local library imports  ==========================
from pychron.envisage.core.core_ui_plugin import CoreUIPlugin

class MDDModelerUIPlugin(CoreUIPlugin):
    '''
    '''
    id = 'pychron.mdd_modeler'

    def _preferences_pages_default(self):
#        from extraction_line_preferences_page import ExtractionLinePreferencesPage
#
#
#        elm = self.application.get_service(EL_PROTOCOL)
#        bind_preference(elm, 'managers', 'pychron.extraction_line')
        from mdd_preferences_page import MDDPreferencesPage
        return [MDDPreferencesPage]

    def _action_sets_default(self):
        '''
        '''
        from mdd_modeler_action_set import MDDModelerActionSet
        return [MDDModelerActionSet]

    def _perspectives_default(self):
        '''
        '''
        from mdd_modeler_perspective import MDDModelerPerspective
        p = [MDDModelerPerspective]
        return p

    def _get_manager(self):
        modeler_manager = self.application.get_service('pychron.modeling.modeler_manager.ModelerManager')
        return modeler_manager

#============= views ===================================
    def _views_default(self):
        '''
        '''
        rv = [self._create_data_directory_view,
              self._create_notes_view,
              self._create_summary_view,
              self._create_process_view,
              self._create_info_view
              ]
        return rv

    def _create_process_view(self, **kw):
        from process_view import ProcessView
        obj = ProcessView()
        manager = self._get_manager()
        if manager is not None:
#            manager.on_trait_change(obj.update_process, 'active_process')
#            manager.on_trait_change(obj.update_state, 'process_state')
            manager.on_trait_change(obj.update_plist, 'fortran_processes[]')
#            manager.on_trait_change(obj.update_state, 'active_processes.state')

        args = dict(id='pychron.modeler.process_view',
                  name='Process',
                  obj=obj
                  )

        return self.traitsuiview_factory(args, kw)

    def _create_summary_view(self, **kw):
        from summary_view import SummaryView
        obj = SummaryView()
        obj._build_summary()
        manager = self._get_manager()

        if manager is not None:
            manager.on_trait_change(obj.selected_update, 'selected_datum')
            manager.on_trait_change(obj.selected_update, 'selected')

        args = dict(id='pychron.modeler.summary_view',
                  name='Summary',
                  obj=obj
                  )

        return self.traitsuiview_factory(args, kw)

    def _create_notes_view(self, **kw):
        from notes_view import NotesView
        obj = NotesView()
        manager = self._get_manager()
        if manager is not None:
            manager.on_trait_change(obj.selected_update, 'selected_datum')

        args = dict(id='pychron.modeler.notes_view',
                  name='Notes',
                  obj=obj
                  )
        return self.traitsuiview_factory(args, kw)

    def _create_info_view(self, **kw):
        from info_view import InfoView
        obj = InfoView()
        manager = self._get_manager()
        if manager is not None:
            manager.on_trait_change(obj.selected_update, 'selected_datum')

        args = dict(id='pychron.modeler.info_view',
                  name='Info',
                  obj=obj
                  )
        return self.traitsuiview_factory(args, kw)

    def _create_data_directory_view(self, **kw):
        modeler_manager = self._get_manager()

        args = dict(
                    id='pychron.modeler.data_directory',
                  name='Data',
                  view='data_select_view',
                  obj=modeler_manager  # .modeler,
                  )
        return self.traitsuiview_factory(args, kw)

    @on_trait_change('application.gui:started')
    def _started(self, obj, name, old, new):
        '''

        '''
        if new  is True:
            app = self.application
            window = app.workbench.active_window
            manager = app.get_service('pychron.modeling.modeler_manager.ModelerManager')
            manager.window = window
            manager.open_default()

#============= EOF ====================================
