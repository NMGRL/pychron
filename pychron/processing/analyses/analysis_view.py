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
from traits.api import HasTraits, Instance, Event, Str
from traitsui.api import View, UItem, InstanceEditor, VGroup, Tabbed, Spring, Group

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.processing.analyses.view.detector_ic_view import DetectorICView
from pychron.processing.analyses.view.error_components_view import ErrorComponentsView
from pychron.processing.analyses.view.peak_center_view import PeakCenterView
from pychron.processing.analyses.view.snapshot_view import SnapshotView
from pychron.processing.analyses.view.spectrometer_view import SpectrometerView
from pychron.processing.analyses.view.text_view import ExperimentView, ExtractionView, MeasurementView
from pychron.processing.analyses.view.history_view import HistoryView
from pychron.processing.analyses.view.interferences_view import InterferencesView
from pychron.processing.analyses.view.main_view import MainView


# class ViewAdapter(TabularAdapter):
#     columns = [('', 'view')]
#
#     view_text = Property
#
#     def _get_view_text(self, *args, **kw):
#         return self.item.name


# class ViewSelection(HasTraits):
#     subviews = List
#     selected_view = Any
#
#     def traits_view(self):
#         v = View(UItem('subviews', editor=TabularEditor(adapter=ViewAdapter(),
#                                                         editable=False,
#                                                         selected='selected_view')))
#         return v
#

class AnalysisView(HasTraits):
    selection_tool = Instance('pychron.processing.analyses.analysis_view.ViewSelection')

    refresh_needed = Event
    analysis_id = Str

    main_view = Instance('pychron.processing.analyses.view.main_view.MainView')
    history_view = Instance('pychron.processing.analyses.view.history_view.HistoryView')
    experiment_view = Instance(ExperimentView)
    interference_view = Instance(InterferencesView)
    measurement_view = Instance(MeasurementView)
    extraction_view = Instance(ExtractionView)
    snapshot_view = Instance(SnapshotView)
    detector_ic_view = Instance(DetectorICView)
    spectrometer_view = Instance(SpectrometerView)
    peak_center_view = Instance(PeakCenterView)
    error_comp_view = Instance(ErrorComponentsView)

    def update_fontsize(self, view, size):
        if 'main' in view:
            v = self.main_view
            view = view.split('.')[-1]
            adapter = getattr(v, '{}_adapter'.format(view))
            adapter.font = 'arial {}'.format(size)
        else:
            v = getattr(self, '{}_view'.format(view))
            if v is not None:
                v.fontsize = size

    def load(self, an):
        analysis_type = an.analysis_type
        analysis_id = an.record_id

        main_view = MainView(an, analysis_type=analysis_type, analysis_id=analysis_id)
        self.main_view = main_view

        self._make_subviews(an)
        # history_view = HistoryView(an)
        # self.history_view = history_view
        #
        # self.analysis_id = analysis_id
        #
        # history_view = self.history_view
        # if history_view is None:
        #     history_view = HistoryView(an)
        #     self.history_view = history_view
        #     history_view.on_trait_change(self.handle_blank_right_clicked, 'blank_right_clicked')
        #
        # views = self._make_subviews(an)
        #
        # main_view = self.main_view
        # if main_view is None:
        #     main_view = MainView(an, analysis_type=analysis_type, analysis_id=analysis_id)
        #     self.main_view = main_view
        #
        # else:
        #     self.main_view.load(an, refresh=True)
        #
        # subviews = [main_view,
        #             history_view] + views
        #

        # self.selection_tool = ViewSelection(subviews=subviews,
        #                                     selected_view=main_view)

    def _make_subviews(self, an):
        for args in (('history', HistoryView),
                     ('experiment', ExperimentView, 'experiment_txt'),
                     ('extraction', ExtractionView, 'extraction_script_blob'),
                     ('measurement', MeasurementView, 'measurement_script_blob'),
                     ('interference', InterferencesView, 'interference_corrections'),
                     ('spectrometer', SpectrometerView, 'source_parameters')):

            if len(args) == 2:
                vname, klass = args
                tattr = None
            else:
                vname, klass, tattr = args

            if tattr:
                if not getattr(an, tattr):
                    continue

            name = '{}_view'.format(vname)
            # view = getattr(self, name)
            # if view is None:
            view = klass(an)
            setattr(self, name, view)

        if an.snapshots:
            snapshot_view = SnapshotView(an.snapshots)
            self.snapshot_view = snapshot_view

        if an.analysis_type == 'detector_ic':
            det_view = DetectorICView(an)
            self.detector_ic_view = det_view

        if an.analysis_type in ('unknown', 'cocktail'):
            self.error_comp_view = ErrorComponentsView(an)

        pch = PeakCenterView()
        if pch.load(an):
            self.peak_center_view = pch

    def traits_view(self):
        main_grp = Group(UItem('main_view', style='custom',
                               editor=InstanceEditor()), label='Main')
        history_grp = Group(UItem('history_view', style='custom',
                                  editor=InstanceEditor()), label='History')

        experiment_grp = Group(UItem('experiment_view', style='custom',
                                     editor=InstanceEditor()), defined_when='experiment_view', label='Experiment')
        interference_grp = Group(UItem('interference_view', style='custom',
                                       editor=InstanceEditor()), defined_when='interference_view', label='Interference')
        measurement_grp = Group(UItem('measurement_view', style='custom',
                                      editor=InstanceEditor()),
                                defined_when='measurement_view',
                                label='Measurement')
        extraction_grp = Group(UItem('extraction_view', style='custom',
                                     editor=InstanceEditor()),
                               defined_when='extraction_view',
                               label='Extraction')
        snapshot_grp = Group(UItem('snapshot_view', style='custom',
                                   editor=InstanceEditor()),
                             defined_when='snapshot_view',
                             label='Snapshot')
        detector_ic_grp = Group(UItem('detector_ic_view', style='custom',
                                      editor=InstanceEditor()),
                                defined_when='detector_ic_view',
                                label='DetectorIC')
        spectrometer_grp = Group(UItem('spectrometer_view', style='custom',
                                       editor=InstanceEditor()), defined_when='spectrometer_view', label='Spectrometer')

        peak_center_grp = Group(UItem('peak_center_view', style='custom',
                                      editor=InstanceEditor()),
                                defined_when='peak_center_view', label='Peak_center')
        v = View(VGroup(Spring(springy=False, height=-10),
                        Tabbed(main_grp, history_grp,
                               experiment_grp,
                               extraction_grp,
                               measurement_grp,
                               peak_center_grp,
                               interference_grp,
                               spectrometer_grp,
                               detector_ic_grp,
                               snapshot_grp)))
        return v
        #
        # v = View(UItem('object.selection_tool.selected_view', style='custom',
        #                editor=InstanceEditor()))
        # return v

    def handle_blank_right_clicked(self, new):
        print 'asdf', new


class DBAnalysisView(AnalysisView):
    pass

# ============= EOF =============================================
