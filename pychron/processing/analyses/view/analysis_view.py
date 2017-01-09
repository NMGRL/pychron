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
from traits.api import HasTraits, Instance, Event, Str, Bool, List
from traitsui.api import View, UItem, InstanceEditor, VGroup, Tabbed, Group, Handler, spring, HGroup

from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.processing.analyses.view.adapters import IsotopeTabularAdapter, IntermediateTabularAdapter
from pychron.processing.analyses.view.detector_ic_view import DetectorICView
from pychron.processing.analyses.view.dvc_commit_view import HistoryView
from pychron.processing.analyses.view.error_components_view import ErrorComponentsView
from pychron.processing.analyses.view.interferences_view import InterferencesView
from pychron.processing.analyses.view.main_view import MainView
from pychron.processing.analyses.view.peak_center_view import PeakCenterView
from pychron.processing.analyses.view.snapshot_view import SnapshotView
from pychron.processing.analyses.view.spectrometer_view import SpectrometerView
from pychron.processing.analyses.view.text_view import ExperimentView, ExtractionView, MeasurementView
from pychron.pychron_constants import DETECTOR_IC, COCKTAIL, UNKNOWN


class AnalysisViewHandler(Handler):
    def show_isotope_evolution(self, uiinfo, obj):
        obj.show_iso_evolutions()

    def show_isotope_evolution_with_sniff(self, uiinfo, obj):
        obj.show_iso_evolutions(show_equilibration=True)

    def show_isotope_evolution_with_baseline(self, uiinfo, obj):
        obj.show_iso_evolutions(show_baseline=True)

    def show_baseline(self, uiinfo, obj):
        obj.show_iso_evolutions(show_evo=False, show_baseline=True)

    def show_sniff(self, uiinfo, obj):
        obj.show_iso_evolutions(show_evo=False, show_equilibration=True)

    def show_all(self, uiinfo, obj):
        obj.show_iso_evolutions(show_evo=True, show_equilibration=True, show_baseline=True)


class AnalysisView(HasTraits):
    # application = Any
    model = Instance('pychron.processing.analyses.analysis.Analysis')
    # selection_tool = Instance('pychron.processing.analyses.analysis_view.ViewSelection')
    selected = List
    refresh_needed = Event
    analysis_id = Str
    dclicked = Event

    main_view = Instance('pychron.processing.analyses.view.main_view.MainView')
    history_view = Instance(HistoryView)
    # isotopes_view = Instance(IsotopeView)

    experiment_view = Instance(ExperimentView)
    interference_view = Instance(InterferencesView)
    measurement_view = Instance(MeasurementView)
    extraction_view = Instance(ExtractionView)
    snapshot_view = Instance(SnapshotView)
    detector_ic_view = Instance(DetectorICView)
    spectrometer_view = Instance(SpectrometerView)
    peak_center_view = Instance(PeakCenterView)
    error_comp_view = Instance(ErrorComponentsView)

    isotopes = List
    isotope_adapter = Instance(IsotopeTabularAdapter, ())
    intermediate_adapter = Instance(IntermediateTabularAdapter, ())
    show_intermediate = Bool(True)

    def show_iso_evolutions(self, show_evo=True, show_equilibration=False, show_baseline=False):
        isotopes = self.selected
        print 'selected isootpes', isotopes
        self.model.show_isotope_evolutions(isotopes, show_evo=show_evo,
                                           show_equilibration=show_equilibration, show_baseline=show_baseline)

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
        self.model = an
        analysis_type = an.analysis_type
        analysis_id = an.record_id
        self.analysis_id = analysis_id

        main_view = MainView(an, analysis_type=analysis_type, analysis_id=analysis_id)
        self.main_view = main_view
        self._make_subviews(an)

        self.isotopes = [an.isotopes[k] for k in an.isotope_keys]

    def _make_subviews(self, an):
        for args in (
                ('history', HistoryView),
                # ('blanks', BlanksView),
                # ('fits', FitsView),
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

        if an.analysis_type == DETECTOR_IC:
            det_view = DetectorICView(an)
            self.detector_ic_view = det_view

        if an.analysis_type in (UNKNOWN, COCKTAIL):
            self.error_comp_view = ErrorComponentsView(an)

        pch = PeakCenterView()
        if pch.load(an):
            self.peak_center_view = pch

    def _dclicked_fired(self, new):
        if new:
            item = new.item
            self.model.show_isotope_evolutions((item,))

    def traits_view(self):
        main_grp = Group(UItem('main_view', style='custom',
                               editor=InstanceEditor()), label='Main')

        teditor = myTabularEditor(adapter=self.isotope_adapter,
                                  drag_enabled=False,
                                  stretch_last_section=False,
                                  editable=False,
                                  multi_select=True,
                                  selected='selected',
                                  dclicked='dclicked',
                                  refresh='refresh_needed')
        ieditor = myTabularEditor(adapter=self.intermediate_adapter,
                                  editable=False,
                                  drag_enabled=False,
                                  stretch_last_section=False,
                                  refresh='refresh_needed')
        isotope_grp = Group(UItem('isotopes',
                                  editor=teditor, ),
                            UItem('isotopes',
                                  editor=ieditor,
                                  visible_when='show_intermediate'),
                            label='Isotopes')

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
        v = View(VGroup(spring,
                        HGroup(spring, UItem('analysis_id', style='readonly'), spring),
                        Tabbed(main_grp,
                               isotope_grp,
                               history_grp,
                               experiment_grp,
                               extraction_grp,
                               measurement_grp,
                               peak_center_grp,
                               interference_grp,
                               spectrometer_grp,
                               detector_ic_grp,
                               snapshot_grp)),
                 handler=AnalysisViewHandler())
        return v


class DBAnalysisView(AnalysisView):
    pass

# ============= EOF =============================================
