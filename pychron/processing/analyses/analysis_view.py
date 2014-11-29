# ===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import HasTraits, List, Property, Any, Instance, Event, Str
from traitsui.api import View, UItem, InstanceEditor, TabularEditor
from traitsui.tabular_adapter import TabularAdapter

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.processing.analyses.view.detector_ic_view import DetectorICView
from pychron.processing.analyses.view.error_components_view import ErrorComponentsView
from pychron.processing.analyses.view.snapshot_view import SnapshotView
from pychron.processing.analyses.view.text_view import ExperimentView, ExtractionView, MeasurementView
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
    analysis_id = Str

    main_view = Instance('pychron.processing.analyses.view.main_view.MainView')
    history_view = Instance('pychron.processing.analyses.view.history_view.HistoryView')
    _experiment_view = None
    _interference_view = None
    _measurement_view = None
    _extraction_view = None
    _snapshot_view = None
    _detector_ic_view = None

    def update_fontsize(self, view, size):
        if 'main' in view:
            v = self.main_view
            view = view.split('.')[-1]
            adapter = getattr(v, '{}_adapter'.format(view))
            adapter.font = 'arial {}'.format(size)
        else:
            v = getattr(self, '_{}_view'.format(view))
            if v is not None:
                v.fontsize = size

    def load(self, an):
        analysis_type = an.analysis_type
        analysis_id = an.record_id

        self.analysis_id = analysis_id

        history_view = self.history_view
        if history_view is None:
            history_view = HistoryView(an)
            self.history_view = history_view
            history_view.on_trait_change(self.handle_blank_right_clicked, 'blank_right_clicked')

        views = self._make_subviews(an)

        main_view = self.main_view
        if main_view is None:
            main_view = MainView(an, analysis_type=analysis_type, analysis_id=analysis_id)
            self.main_view = main_view

        else:
            self.main_view.load(an, refresh=True)

        subviews = [main_view,
                    history_view] + views

        if analysis_type in ('unknown', 'cocktail'):
            subviews.append(ErrorComponentsView(an))

        pch = PeakCenterView()
        if pch.load(an):
            subviews.append(pch)

        self.selection_tool = ViewSelection(subviews=subviews,
                                            selected_view=main_view)

    def _make_subviews(self, an):
        views = []
        for vname, klass in (('experiment', ExperimentView),
                             ('extraction', ExtractionView),
                             ('measurement', MeasurementView),
                             ('interference', InterferencesView)):
            name = '_{}_view'.format(vname)
            view = getattr(self, name)
            if view is None:
                view = klass(an)
            setattr(self, name, view)
            views.append(view)

        snapshot_view = self._snapshot_view
        if snapshot_view is None and an.snapshots:
            snapshot_view = SnapshotView(an.snapshots)
            self._snapshot_view = snapshot_view
            views.append(snapshot_view)

        if an.analysis_type == 'detector_ic':
            det_view = self._detector_ic_view
            if det_view is None:
                det_view = DetectorICView(an)
                self._detector_ic_view = det_view
                views.append(det_view)

        return views

    def traits_view(self):
        v = View(UItem('object.selection_tool.selected_view', style='custom',
                       editor=InstanceEditor()))
        return v

    def handle_blank_right_clicked(self, new):
        print 'asdf', new


class DBAnalysisView(AnalysisView):
    pass


# ============= EOF =============================================
