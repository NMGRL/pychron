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

class CanvasDesignerUIPlugin(CoreUIPlugin):
    '''
        G{classtree}
    '''
    id = 'pychron.canvas_designer.ui'


    def _action_sets_default(self):
        '''
        '''
        from canvas_designer_action_set import CanvasDesignerActionSet
        return [CanvasDesignerActionSet]

    def _perspectives_default(self):
        '''
        '''
        p = []
        return p

    @on_trait_change('application.gui:started')
    def _started(self, obj, name, old, new):
        '''
            @type obj: C{str}
            @param obj:

            @type name: C{str}
            @param name:

            @type old: C{str}
            @param old:

            @type new: C{str}
            @param new:
        '''
        if new  is True:
            app = self.application
            window = app.workbench.active_window
            manager = app.get_service('pychron.canvas.designer.canvas_manager.CanvasManager')
            manager.window = window
            debug = False
            if debug:
                manager.open_default()
#============= views ===================================
    def _views_default(self):
        '''
        '''
        rv = [self._create_property_view]
        return rv
    def _create_property_view(self, **kw):
        '''
            @type **kw: C{str}
            @param **kw:
        '''
        app = self.application
        obj = app.get_service('pychron.canvas.designer.canvas_manager.CanvasManager')
        args = dict(id='pychron.canvas_designer.property_view',
                         name='Property View',
                         obj=obj,
                         view='active_canvas_view',
                         )

        return self.traitsuiview_factory(args, kw)
#    def _create_designer_view(self, window, **kw):
#        obj = CanvasDesigner()
#        v = TraitsUIView(id = 'pychron.canvas_designer.ui',
#                         category = 'Canvas',
#                         name = 'Canvas Designer',
#                         obj = obj,
#                         window = window,
#                         **kw
#                         )
#        return v

#============= EOF ====================================
