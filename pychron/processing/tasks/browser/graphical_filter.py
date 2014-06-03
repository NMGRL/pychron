# ===============================================================================
# Copyright 2014 Jake Ross
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
from pychron.core.ui import set_qt

set_qt()

# ============= enthought library imports =======================
from traits.api import HasTraits, Instance, List, Int, Bool
from traitsui.menu import Action
from traitsui.api import View, Controller, UItem, HGroup, CheckListEditor, VGroup, Item
from chaco.tools.api import RangeSelection, RangeSelectionOverlay
from chaco.scales.api import CalendarScaleSystem
from chaco.scales_tick_generator import ScalesTickGenerator
from chaco.tools.broadcaster import BroadcasterTool
# ============= standard library imports ========================
from numpy import array
#============= local library imports  ==========================
from pychron.graph.graph import Graph
from pychron.processing.plotters.series.ticks import tick_formatter, StaticTickGenerator, TICKS
from pychron.experiment.utilities.identifier import ANALYSIS_MAPPING_INTS, ANALYSIS_MAPPING
from pychron.graph.tools.analysis_inspector import AnalysisPointInspector
from pychron.graph.tools.point_inspector import PointInspectorOverlay

REVERSE_ANALYSIS_MAPPING = {v: k for k, v in ANALYSIS_MAPPING_INTS.items()}


def get_analysis_type(x):
    return REVERSE_ANALYSIS_MAPPING[x]


ANALYSIS_NAMES = [(a.split(':')[1] if ':' in a else a) for a in ANALYSIS_MAPPING.values()]


class SelectionGraph(Graph):
    def setup(self, x, y, ans):
        p = self.new_plot()
        p.padding_left = 60
        p.y_axis.tick_label_formatter = tick_formatter
        p.y_axis.tick_generator = StaticTickGenerator()
        p.y_axis.title = 'Analysis Type'
        p.x_axis.tick_generator = ScalesTickGenerator(scale=CalendarScaleSystem())
        p.x_axis.title = 'Time'
        p.index_range.tight_bounds = False
        # p.y_axis.tick_label_rotate_angle = 45
        self.set_y_limits(min_=-1, max_=len(TICKS))

        scatter, _ = self.new_series(x, y, type='scatter', marker_size=1)

        broadcaster = BroadcasterTool()
        scatter.tools.append(broadcaster)

        point_inspector = AnalysisPointInspector(scatter,
                                                 analyses=ans,
                                                 value_format=get_analysis_type,
                                                 additional_info=lambda x: ('Time={}'.format(x.rundate),
                                                                            'Project={}'.format(x.project)))

        pinspector_overlay = PointInspectorOverlay(component=scatter,
                                                   tool=point_inspector)

        range_selector = RangeSelection(scatter, left_button_selects=True)
        broadcaster.tools.append(point_inspector)
        broadcaster.tools.append(range_selector)

        scatter.overlays.append(RangeSelectionOverlay(component=scatter))
        scatter.overlays.append(pinspector_overlay)

        self.scatter = scatter

    def get_selection_mask(self):
        try:
            return self.scatter.index.metadata['selection_masks'][0]
        except KeyError:
            pass


class GraphicalFilterModel(HasTraits):
    graph = Instance(SelectionGraph, ())
    analyses = List
    analysis_types = List(['Unknown'])
    available_analysis_types = List(ANALYSIS_NAMES)
    exclusion_pad = Int(20)
    use_project_exclusion = Bool
    projects = List
    is_append = True

    def setup(self):
        f = lambda x: ANALYSIS_MAPPING_INTS[x] if x in ANALYSIS_MAPPING_INTS else -1

        ans = self._filter_projects(self.analyses)

        x, y = zip(*[(ai.timestamp, f(ai.analysis_type)) for ai in ans])
        self.graph.setup(x, y, ans)

    def get_selection(self):
        mask = self.graph.get_selection_mask()

        if mask is not None:
            a = array(self.analyses)
            ans = a[mask]
        else:
            ans = self.analyses

        return self._filter_analysis_types(ans)

    def _filter_projects(self, ans):
        if not self.projects or not self.use_project_exclusion:
            return ans

        def gen():
            projects = self.projects

            def test(a):
                """
                    is ai within X hours of an analysis from projects
                """
                at = a.analysis_timestamp
                threshold = 3600. * self.exclusion_pad
                idx = ans.index(a)
                # search backwards
                for i in xrange(idx - 1, -1, -1):
                    ta = ans[i]
                    if abs(ta.analysis_timestamp - at) > threshold:
                        return
                    elif ta.project in projects:
                        return True
                #search forwards
                for i in xrange(idx, len(ans), 1):
                    ta = ans[i]
                    if abs(ta.analysis_timestamp - at) > threshold:
                        return
                    elif ta.project in projects:
                        return True

            for ai in ans:
                if ai.project == ('references', 'j-curve'):
                    if test(ai):
                        yield ai
                elif ai.project in projects:
                    yield ai

        return list(gen())

    def _filter_analysis_types(self, ans):
        """
            only use analyses with analysis_type in self.analyses_types
        """
        ats = map(str.lower, self.analysis_types)
        f = lambda x: x.analysis_type.lower() in ats
        return filter(f, ans)


class GraphicalFilterView(Controller):
    def append_action(self):
        self.info.ui.dispose(result=True)
        self.info.object.is_append = True

    def replace_action(self):
        self.info.ui.dispose(result=True)
        self.info.object.is_append = False

    def traits_view(self):
        ctrl_grp = VGroup(HGroup(UItem('use_project_exclusion'),
                                 Item('exclusion_pad',
                                      enabled_when='use_project_exclusion')),
                          UItem('analysis_types',
                                style='custom',
                                editor=CheckListEditor(cols=1,
                                                       name='available_analysis_types')))

        v = View(HGroup(ctrl_grp,
                        UItem('graph', style='custom')),
                 buttons=['Cancel',
                          Action(name='Replace', on_perform=self.replace_action),
                          Action(name='Append', on_perform=self.append_action)],
                 kind='livemodal',
                 resizable=True)
        return v


from traits.api import Button


class Demo(HasTraits):
    test_button = Button

    def traits_view(self):
        return View('test_button')

    def _test_button_fired(self):
        g = GraphicalFilterModel(analyses=ans)
        g.setup()
        gv = GraphicalFilterView(model=g)

        info = gv.edit_traits()
        print info.result
        if info.result:
            s = g.get_selection()
            for si in s:
                print si, si.analysis_type


if __name__ == '__main__':
    from pychron.database.isotope_database_manager import IsotopeDatabaseManager
    from pychron.database.records.isotope_record import IsotopeRecordView

    man = IsotopeDatabaseManager(bind=False, connect=False)
    db = man.db
    db.trait_set(name='pychrondata_dev',
                 kind='mysql',
                 username='root',
                 password='Argon',
                 echo=False)
    db.connect()

    with db.session_ctx():
        # for si in sams:
        ans, n = db.get_labnumber_analyses([
            '57493',
        ])
        ts = [ai.analysis_timestamp for ai in ans]
        lpost, hpost = min(ts), max(ts)
        ans = db.get_date_range_analyses(lpost, hpost)
        ans = [IsotopeRecordView(ai) for ai in ans]
        ans = sorted(ans, key=lambda x: x.timestamp)

    d = Demo()
    d.configure_traits()
    # print info.result
    # if info.result:
    # s = g.get_selection()
    #     for si in s:
    #         print si, si.analysis_type
#============= EOF =============================================

