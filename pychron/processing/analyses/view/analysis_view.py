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


from traits.api import HasTraits, Instance, Event, Str, Bool, List, Any, on_trait_change
from traitsui.api import (
    View,
    UItem,
    VGroup,
    Group,
    Handler,
    spring,
    HGroup,
    ListEditor,
    Spring,
)

from pychron.core.helpers.binpack import unpack
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.graph.stacked_graph import StackedGraph
from pychron.processing.analyses.view.adapters import (
    IsotopeTabularAdapter,
    IntermediateTabularAdapter,
)
from pychron.processing.analyses.view.detector_ic_view import DetectorICView
from pychron.processing.analyses.view.dvc_commit_view import HistoryView
from pychron.processing.analyses.view.error_components_view import ErrorComponentsView
from pychron.processing.analyses.view.icfactor_view import ICFactorView
from pychron.processing.analyses.view.interferences_view import InterferencesView
from pychron.processing.analyses.view.main_view import MainView
from pychron.processing.analyses.view.peak_center_view import PeakCenterView
from pychron.processing.analyses.view.regression_view import RegressionView
from pychron.processing.analyses.view.sample_view import SampleView
from pychron.processing.analyses.view.snapshot_view import SnapshotView
from pychron.processing.analyses.view.spectrometer_view import SpectrometerView
from pychron.processing.analyses.view.text_view import ExperimentView, MeasurementView
from pychron.pychron_constants import DETECTOR_IC, COCKTAIL, UNKNOWN


class AnalysisViewHandler(Handler):
    def show_isotope_evolution(self, uiinfo, obj):
        # obj.show_iso_evolutions()
        obj.updated = {}

    def show_isotope_evolution_with_sniff(self, uiinfo, obj):
        obj.updated = {"show_equilibration": True}
        # obj.show_iso_evolutions(show_equilibration=True)

    def show_isotope_evolution_with_baseline(self, uiinfo, obj):
        # obj.show_iso_evolutions(show_baseline=True)
        obj.updated = {"show_baseline": True}

    def show_residuals(self, uiinfo, obj):
        obj.updated = {"show_residuals": True}

    def show_equilibration_inspector(self, uiinfo, obj):
        obj.updated = {"show_equilibration_inspector": True}

    def show_inspection(self, uiinfo, obj):
        obj.updated = {"show_inspection": True}

    def show_baseline(self, uiinfo, obj):
        obj.updated = {"show_evo": False, "show_baseline": True}
        # obj.show_iso_evolutions(show_evo=False, show_baseline=True)

    def show_sniff(self, uiinfo, obj):
        obj.updated = {"show_evo": False, "show_equilibration": True}
        # obj.show_iso_evolutions(show_evo=False, show_equilibration=True)

    def show_all(self, uiinfo, obj):
        obj.updated = {
            "show_evo": True,
            "show_equilibration": True,
            "show_baseline": True,
        }
        # obj.show_iso_evolutions(show_evo=True, show_equilibration=True, show_baseline=True)


class MetaView(HasTraits):
    name = "Meta"
    spectrometer = Instance(SpectrometerView)
    interference = Instance(InterferencesView)
    sample = Instance(SampleView)

    def traits_view(self):
        v = View(
            VGroup(
                VGroup(
                    UItem("spectrometer", style="custom"),
                    show_border=True,
                    label="Spectrometer",
                ),
                VGroup(
                    UItem("interference", style="custom"),
                    show_border=True,
                    label="Reactor",
                ),
                VGroup(
                    UItem("sample", style="custom"),
                    show_border=True,
                    label="Sample",
                ),
            )
        )
        return v


class IsotopeView(HasTraits):
    name = "Isotopes"
    isotopes = List
    isotope_adapter = Instance(IsotopeTabularAdapter, ())
    intermediate_adapter = Instance(IntermediateTabularAdapter, ())
    show_intermediate = Bool(True)
    updated = Event
    dclicked = Event
    selected = List

    def _dclicked_fired(self, new):
        if new:
            # item = new.item
            self.updated = {}
            # self.model.show_isotope_evolutions((item,))

    def traits_view(self):
        teditor = myTabularEditor(
            adapter=self.isotope_adapter,
            drag_enabled=False,
            stretch_last_section=False,
            editable=False,
            multi_select=True,
            selected="selected",
            dclicked="dclicked",
            refresh="refresh_needed",
        )
        ieditor = myTabularEditor(
            adapter=self.intermediate_adapter,
            editable=False,
            drag_enabled=False,
            stretch_last_section=False,
            refresh="refresh_needed",
        )
        isotope_grp = Group(
            UItem(
                "isotopes",
                editor=teditor,
            ),
            UItem("isotopes", editor=ieditor, visible_when="show_intermediate"),
        )
        v = View(isotope_grp, handler=AnalysisViewHandler())
        return v


class ExtractionView(HasTraits):
    graph = Instance(StackedGraph)
    name = "Extraction"
    refresh_needed = Event

    def setup_graph(self, response_data, request_data, setpoint_data):
        self.graph = g = StackedGraph(container_dict={"spacing": 10})
        ret = False
        pid = 0
        if response_data:
            try:
                x, y = unpack(response_data, fmt="<ff", decode=True)
                if x[1:]:
                    p = g.new_plot()
                    p.value_range.tight_bounds = False
                    g.set_x_title("Time (s)")
                    g.set_y_title("Temp C")
                    g.new_series(x[1:], y[1:])
                    pid += 1
                    ret = True

                    if setpoint_data:
                        x, y = unpack(setpoint_data, fmt="<ff", decode=True)
                        if x[1:]:
                            g.new_series(x[1:], y[1:])

            except ValueError:
                pass

        if request_data:
            try:
                x, y = unpack(request_data, fmt="<ff", decode=True)
                if x[1:]:
                    p = self.graph.new_plot()

                    g.set_x_title("Time")
                    g.set_y_title("% Power")
                    g.new_series(x[1:], y[1:])
                    g.set_y_limits(min_=0, max_=max(y) * 1.1, plotid=pid)
                    ret = True
            except ValueError:
                pass

        return ret

    def traits_view(self):
        v = View(UItem("graph", style="custom"))
        return v


class AnalysisView(HasTraits):
    # application = Any
    model = Instance("pychron.processing.analyses.analysis.Analysis")
    # selection_tool = Instance('pychron.processing.analyses.analysis_view.ViewSelection')
    analysis_id = Str
    selected_tab = Any

    main_view = Instance(MainView, ())

    experiment_view = Instance(ExperimentView)
    measurement_view = Instance(MeasurementView)
    extraction_view = Instance(ExtractionView)
    isotope_view = Instance(IsotopeView, ())

    groups = List

    def show_iso_evolutions(
        self,
        show_evo=True,
        show_equilibration=False,
        show_baseline=False,
        show_inspection=False,
        show_residuals=False,
        show_equilibration_inspector=False,
    ):
        isotopes = self.isotope_view.selected
        return self.model.show_isotope_evolutions(
            isotopes,
            show_evo=show_evo,
            show_equilibration=show_equilibration,
            show_baseline=show_baseline,
            show_inspection=show_inspection,
            show_residuals=show_residuals,
            show_equilibration_inspector=show_equilibration_inspector,
        )

    def update_fontsize(self, view, size):
        if "main" in view:
            v = self.main_view
            view = view.split(".")[-1]
            adapter = getattr(v, "{}_adapter".format(view))
            adapter.font = "arial {}".format(size)
        else:
            v = getattr(self, "{}_view".format(view))
            if v is not None:
                v.fontsize = size

    def load(self, an, quick=False):
        self.groups = []
        self.model = an
        analysis_type = an.analysis_type
        self.analysis_id = analysis_id = "{}({})".format(an.record_id, an.sample)

        # main_view = MainView(an, analysis_type=analysis_type, analysis_id=analysis_id)
        self.main_view.trait_set(analysis_type=analysis_type, analysis_id=analysis_id)
        self.main_view.load(an)
        # self.main_view = main_view
        # self.groups.append(self.main_view)

        isos = [an.isotopes[k] for k in an.isotope_keys]
        # iso_view = IsotopeView(isotopes=isos)
        self.isotope_view.isotopes = isos
        # self.groups.append(self.isotope_view)

        gs = [self.main_view, self.isotope_view]
        if not quick:
            self._make_subviews(an, gs)

        # self.selected_tab = self.main_view
        self.groups = gs
        # do_after(50, self.trait_set, selected_tab=self.main_view)

    def refresh(self):
        an = self.model
        self.isotope_view.isotopes = []
        isos = [an.isotopes[k] for k in an.isotope_keys]
        self.isotope_view.isotopes = isos
        self.isotope_view.refresh_needed = True

        self.main_view.load_computed(self.model, new_list=False)
        self.main_view.refresh_needed = True

        for g in self.groups:
            if isinstance(g, ErrorComponentsView):
                g.load(self.model)

    @on_trait_change("isotope_view:updated")
    def show_iso_evo(self, new):
        g = self.show_iso_evolutions(**new)
        g.on_trait_change(self.refresh, "grouping")

    def _selected_tab_changed(self, new):
        if isinstance(new, HistoryView):
            new.initialize(self.model)
            new.dvc = self.dvc
        elif isinstance(new, RegressionView):
            new.initialize(self.model)
        elif isinstance(new, ICFactorView):
            new.dvc = self.dvc
            new.activate()

    def _make_subviews(self, an, gs):
        view = HistoryView()
        gs.append(view)

        view = MetaView(
            interference=InterferencesView(an),
            spectrometer=SpectrometerView(an),
            sample=SampleView(an),
        )
        gs.append(view)

        view = RegressionView()
        gs.append(view)
        if an.measured_response_stream:
            ev = ExtractionView()
            if ev.setup_graph(
                an.measured_response_stream,
                an.requested_output_stream,
                an.setpoint_stream,
            ):
                gs.append(ev)

        if an.snapshots:
            snapshot_view = SnapshotView(an.snapshots)
            gs.append(snapshot_view)

        if an.analysis_type == DETECTOR_IC:
            det_view = DetectorICView(an)
            gs.append(det_view)

        if an.analysis_type in (UNKNOWN, COCKTAIL):
            ecv = ErrorComponentsView(an)
            gs.append(ecv)

            icv = ICFactorView(analysis=an)
            gs.append(icv)

        pch = PeakCenterView()
        if pch.load(an):
            gs.append(pch)

    def traits_view(self):
        v = View(
            VGroup(
                Spring(springy=False, height=10),
                HGroup(spring, UItem("analysis_id", style="readonly"), spring),
                UItem(
                    "groups",
                    style="custom",
                    editor=ListEditor(
                        use_notebook=True, page_name=".name", selected="selected_tab"
                    ),
                ),
            )
        )
        return v


class DBAnalysisView(AnalysisView):
    pass


# ============= EOF =============================================
