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
from traits.api import HasTraits, List, Property, Any, Instance, Event
from traitsui.api import View, UItem, InstanceEditor, TabularEditor
from traitsui.tabular_adapter import TabularAdapter

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.analyses.view.error_components_view import ErrorComponentsView

from pychron.processing.analyses.view.experiment_view import ExperimentView
from pychron.processing.analyses.view.history_view import HistoryView
from pychron.processing.analyses.view.interferences_view import InterferencesView
from pychron.processing.analyses.view.main_view import MainView
from pychron.processing.analyses.view.peak_center_view import PeakCenterView


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

    refresh_needed = Event

    main_view = None
    _experiment_view = None
    _history_view = None
    _interference_view = None

    def load(self, an):
        analysis_type = an.analysis_type
        analysis_id = an.record_id
        self.analysis_id = analysis_id

        history_view = self._history_view
        if history_view is None:
            history_view = HistoryView(an)
            self._history_view = history_view
        experiment_view = self._experiment_view
        if experiment_view is None:
            experiment_view = ExperimentView(an)
            self._experiment_view = experiment_view
        interference_view = self._interference_view
        if interference_view is None:
            interference_view = InterferencesView(an)
            self._interference_view = interference_view
        main_view = self.main_view
        if main_view is None:
            main_view = MainView(an, analysis_type=analysis_type, analysis_id=analysis_id)
            self.main_view = main_view

        else:
            self.main_view.load(an, refresh=True)

        subviews = [main_view,
                    experiment_view,
                    history_view,
                    interference_view]

        if analysis_type in ('unknown', 'cocktail'):
            subviews.append(ErrorComponentsView(an))

        pch = PeakCenterView()
        if pch.load(an):
            subviews.append(pch)

        self.selection_tool = ViewSelection(subviews=subviews,
                                            selected_view=main_view)

    def traits_view(self):
        v = View(UItem('object.selection_tool.selected_view', style='custom',
                       editor=InstanceEditor()))
        return v


class DBAnalysisView(AnalysisView):
    pass


#============= EOF =============================================
