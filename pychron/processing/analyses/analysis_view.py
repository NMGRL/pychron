#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import HasTraits, List, Property, Any, Instance
from traitsui.api import View, UItem, InstanceEditor, TabularEditor
from traitsui.tabular_adapter import TabularAdapter

#============= standard library imports ========================
#============= local library imports  ==========================

from pychron.processing.analyses.view.experiment_view import ExperimentView
from pychron.processing.analyses.view.main_view import MainView


class ViewAdapter(TabularAdapter):
    columns = [('', 'view')]

    view_text = Property

    def _get_view_text(self, *args, **kw):
        return self.item.name


class ViewSelection(HasTraits):
    subviews = List
    selected_view = Any

    def traits_view(self):
        v = View(UItem('subviews', editor=TabularEditor(adapter=ViewAdapter(),
                                                        editable=False,
                                                        selected='selected_view')))
        return v


class AnalysisView(HasTraits):
    selection_tool = Instance('pychron.processing.analyses.analysis_view.ViewSelection')

    def load(self, an):
        analysis_type = an.analysis_type
        analysis_id = an.record_id
        self.analysis_id = analysis_id

        main_view = MainView(an, analysis_type=analysis_type, analysis_id=analysis_id)

        experiment_view = ExperimentView(an)

        subviews = [main_view,
                    experiment_view]

        self.selection_tool = ViewSelection(subviews=subviews,
                                            selected_view=main_view)

    def traits_view(self):
        v = View(UItem('object.selection_tool.selected_view', style='custom',
                       editor=InstanceEditor()))
        return v


class DBAnalysisView(AnalysisView):
    pass


#============= EOF =============================================
