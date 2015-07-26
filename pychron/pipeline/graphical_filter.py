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
# ============= enthought library imports =======================
from datetime import timedelta
from traits.api import HasTraits, Instance, List, Int, Bool, on_trait_change, Button, Str, Any, Float
from traitsui.api import View, Controller, UItem, HGroup, CheckListEditor, VGroup, Item, spring
from chaco.scales.api import CalendarScaleSystem
from chaco.scales_tick_generator import ScalesTickGenerator
from chaco.tools.broadcaster import BroadcasterTool
# ============= standard library imports ========================
from itertools import groupby
import math
# ============= local library imports  ==========================
from pychron.graph.graph import Graph
from pychron.graph.tools.rect_selection_tool import RectSelectionTool, RectSelectionOverlay

from pychron.experiment.utilities.identifier import ANALYSIS_MAPPING_INTS
from pychron.graph.tools.analysis_inspector import AnalysisPointInspector
from pychron.graph.tools.point_inspector import PointInspectorOverlay

REVERSE_ANALYSIS_MAPPING = {v: k.replace('_', ' ') for k, v in ANALYSIS_MAPPING_INTS.items()}


def get_analysis_type(x):
    return REVERSE_ANALYSIS_MAPPING[math.floor(x)]


def analysis_type_func(analyses, offset=True):
    """
    convert analysis type to number

    if offset is True
    use analysis_mapping_ints to convert atype to integer
    then add a fractional value to indicate position in list
    e.g first unknown 1, second unknown 1.1
    fractional value is normalized to 1 so that there is no overlap
    e.i unknown while always be 1.### and never 2.0

    """
    if offset:
        key = lambda x: x.analysis_type
        cans = sorted(analyses, key=key)
        counts = {k: float(len(list(v))) for k, v in groupby(cans, key=key)}

    __cache__ = {}

    def f(x):
        c = 0
        if offset:
            if x in __cache__:
                c = __cache__[x] + 1
            __cache__[x] = c
            c /= counts[x]

        return ANALYSIS_MAPPING_INTS[x] + c if x in ANALYSIS_MAPPING_INTS else -1

    return f


# ANALYSIS_NAMES = [(a.split(':')[1] if ':' in a else a) for a in ANALYSIS_MAPPING.values()]


class SelectionGraph(Graph):
    scatter = None

    def setup(self, x, y, ans):
        from pychron.pipeline.plot.plotter.ticks import tick_formatter, StaticTickGenerator, TICKS

        p = self.new_plot()
        p.padding_left = 60
        p.y_axis.tick_label_formatter = tick_formatter
        p.y_axis.tick_generator = StaticTickGenerator()
        p.y_axis.title = 'Analysis Type'

        # p.y_grid.line_style='solid'
        # p.y_grid.line_color='green'
        # p.y_grid.line_weight = 1.5

        self.set_y_limits(min_=-1, max_=len(TICKS))

        p.index_range.tight_bounds = False
        p.x_axis.tick_generator = ScalesTickGenerator(scale=CalendarScaleSystem())
        p.x_grid.tick_generator = p.x_axis.tick_generator
        p.x_axis.title = 'Time'
        # p.y_axis.tick_label_rotate_angle = 45

        scatter, _ = self.new_series(x, y, type='scatter',
                                     marker_size=1.5,
                                     selection_color='red',
                                     selection_marker='circle',
                                     selection_marker_size=2.5)

        broadcaster = BroadcasterTool()
        scatter.tools.append(broadcaster)

        point_inspector = AnalysisPointInspector(scatter,
                                                 analyses=ans,
                                                 value_format=get_analysis_type,
                                                 additional_info=lambda i, x, y, ai: ('Time={}'.format(ai.rundate),
                                                                                      'Project={}'.format(ai.project)))

        pinspector_overlay = PointInspectorOverlay(component=scatter,
                                                   tool=point_inspector)

        rect_tool = RectSelectionTool(scatter)
        rect_overlay = RectSelectionOverlay(component=scatter,
                                            tool=rect_tool)

        scatter.overlays.append(rect_overlay)
        broadcaster.tools.append(rect_tool)
        # range_selector = RangeSelection(scatter, left_button_selects=True)
        broadcaster.tools.append(point_inspector)
        # broadcaster.tools.append(range_selector)

        # scatter.overlays.append(RangeSelectionOverlay(component=scatter))
        scatter.overlays.append(pinspector_overlay)

        self.scatter = scatter

        # def get_selection_mask(self):
        # sels = self.scatter.index.metadata['selections']

        # d = self.scatter.index.get_data()
        # print d,sels

        # return array([x in sels for x in xrange(d.shape[0])])
        #

        # try:
        #     return self.scatter.index.metadata[''][0]
        # except KeyError, e:
        #     print 'selection mask', e


class GraphicalFilterModel(HasTraits):
    dvc = Any
    graph = Instance(SelectionGraph, ())
    analyses = List
    analysis_types = List(['Unknown'])
    available_analysis_types = List
    toggle_analysis_types = Bool

    exclusion_pad = Int(20)
    use_project_exclusion = Bool
    use_offset_analyses = Bool(True)
    projects = List
    always_exclude_unknowns = Bool(False)
    threshold = Float(1)
    # is_append = True
    # use_all = False

    def setup(self, set_atypes=True):
        self.graph.clear()

        f = analysis_type_func(self.analyses, offset=self.use_offset_analyses)
        # ans = self._filter_projects(self.analyses)

        ans = self.analyses
        if set_atypes:
            def ff(at):
                return ' '.join(map(unicode.capitalize, at.split('_')))

            self.available_analysis_types = list({ff(ai.analysis_type) for ai in ans})
            # if self.always_exclude_unknowns:
            #     try:
            #         self.available_analysis_types.remove('Unknown')
            #     except IndexError:
            #         pass
            # if 'Unknown' in self.available_analysis_types:
            #     self.analysis_types = ['Unknown']
            # else:

        # ans = self._filter_analysis_types(ans)
        if ans:
            # todo: CalendarScaleSystem off by 1 hour. add 3600 as a temp hack
            x, y = zip(*[(ai.timestamp + 3600, f(ai.analysis_type)) for ai in sorted(ans, key=lambda x: x.timestamp)])
            # x, y = zip(*[(ai.timestamp, f(ai.analysis_type)) for ai in ans])
        else:
            x, y, ans = [], [], []

        self.graph.setup(x, y, ans)

    def get_filtered_selection(self):
        selection = self.graph.scatter.index.metadata['selections']
        ans = self.analyses
        # print selection
        if selection:
            ans = (ai for i, ai in enumerate(ans) if i not in selection)

        return self._filter_analysis_types(ans)

    def search_backward(self):
        def func():
            self.low_post = self.low_post - timedelta(hours=self.threshold)

        self.search(func)

    def search_forward(self):
        def func():
            self.high_post = self.high_post + timedelta(hours=self.threshold)

        self.search(func)

    def search(self, func):
        uuids = [a.uuid for a in self.analyses]
        for i in range(10):
            records = self.dvc.find_references([self.low_post, self.high_post],
                                               [x.lower().replace(' ', '_') for x in self.analysis_types],
                                               self.threshold,
                                               exclude=uuids)
            func()
            if records:
                self.analyses.extend(records)
                self.setup()
                break

    def _filter_analysis_types(self, ans):
        """
            only use analyses with analysis_type in self.analyses_types
        """

        ats = map(lambda x: x.lower().replace(' ', '_'), map(str.lower, self.analysis_types))
        f = lambda x: x.analysis_type.lower() in ats
        ans = filter(f, ans)
        return ans

    def _toggle_analysis_types_changed(self):
        if self.toggle_analysis_types:
            val = self.available_analysis_types
        else:
            val = []

        self.trait_set(analysis_types=val)

    @on_trait_change('use_offset_analyses, analysis_types[]')
    def handle_analysis_types(self):
        self.setup(set_atypes=False)

class GraphicalFilterView(Controller):
    is_append = Bool
    append_button = Button('Append')
    replace_button = Button('Replace')
    help_str = Str('Select the analyses you want to EXCLUDE')

    search_backward = Button
    search_forward = Button

    def controller_search_backward_changed(self, info):
        self.model.search_backward()

    def controller_search_forward_changed(self, info):
        self.model.search_forward()

    def controller_append_button_changed(self, info):
        self.is_append = True
        self.info.ui.dispose(result=True)

    def controller_replace_button_changed(self, info):
        self.is_append = False
        self.info.ui.dispose(result=True)

    def traits_view(self):
        egrp = HGroup(UItem('use_project_exclusion'),
                                 Item('exclusion_pad',
                                      enabled_when='use_project_exclusion')),
        ctrl_grp = VGroup(HGroup(Item('use_offset_analyses', label='Use Offset')),
                          VGroup(HGroup(Item('toggle_analysis_types', label='Toggle')),
                                 UItem('analysis_types',
                                       tooltip='Only select these types of analyses',
                                       style='custom',
                                       editor=CheckListEditor(cols=1,
                                                              name='available_analysis_types')),
                                 label='Analysis Types',
                                 show_border=True))
        bgrp = HGroup(spring, UItem('controller.append_button'), UItem('controller.replace_button'))
        tgrp = HGroup(UItem('controller.help_str', style='readonly'), show_border=True)
        v = View(VGroup(tgrp,
                        HGroup(UItem('controller.search_backward'),
                               spring,
                               UItem('controller.search_forward')),
                        HGroup(ctrl_grp, UItem('graph', style='custom', width=0.80)),
                        bgrp),
                 title='Graphical Filter',
                 kind='livemodal',
                 resizable=True)
        return v

# ============= EOF =============================================

# def _filter_projects(self, ans):
#     if not self.projects or not self.use_project_exclusion:
#         return ans
#
#     def gen():
#         projects = self.projects
#
#         def test(aa):
#             """
#                 is ai within X hours of an analysis from projects
#             """
#             at = aa.analysis_timestamp
#             threshold = 3600. * self.exclusion_pad
#             idx = ans.index(aa)
#             # search backwards
#             for i in xrange(idx - 1, -1, -1):
#                 ta = ans[i]
#                 if abs(ta.analysis_timestamp - at) > threshold:
#                     return
#                 elif ta.project in projects:
#                     return True
#             # search forwards
#             for i in xrange(idx, len(ans), 1):
#                 ta = ans[i]
#                 if abs(ta.analysis_timestamp - at) > threshold:
#                     return
#                 elif ta.project in projects:
#                     return True
#
#         for ai in ans:
#             if self.use_project_exclusion and ai.project == ('references', 'j-curve'):
#                 if test(ai):
#                     yield ai
#             elif ai.project in projects:
#                 yield ai
#
#     return list(gen())
# if __name__ == '__main__':
#     from traits.api import Button
#
#     class Demo(HasTraits):
#         test_button = Button
#
#         def traits_view(self):
#             return View('test_button')
#
#         def _test_button_fired(self):
#             g = GraphicalFilterModel(analyses=self.analyses)
#             g.setup()
#             gv = GraphicalFilterView(model=g)
#
#             info = gv.edit_traits()
#             if info.result:
#                 s = g.get_selection()
#                 for si in s:
#                     print si, si.analysis_type
#
#     from pychron.database.isotope_database_manager import IsotopeDatabaseManager
#     from pychron.database.records.isotope_record import IsotopeRecordView
#
#     man = IsotopeDatabaseManager(bind=False, connect=False)
#     db = man.db
#     db.trait_set(name='pychrondata',
#                  kind='mysql',
#                  host='129.138.12.160',
#                  username='root',
#                  password='DBArgon',
#                  echo=False)
#     db.connect()
#
#     with db.session_ctx():
#         # for si in sams:
#         _ans, n = db.get_labnumber_analyses([
#             # '57493',
#             '62118'
#         ])
#         ts = [xi.analysis_timestamp for xi in _ans]
#         lpost, hpost = min(ts), max(ts)
#         _ans = db.get_analyses_by_date_range(lpost, hpost, order='asc')
#         # _ans = db.get_date_range_analyses(lpost, hpost, ordering='asc')
#         _ans = [IsotopeRecordView(xi) for xi in _ans]
#         # _ans = sorted(_ans, key=lambda x: x.timestamp)
#
#     d = Demo(analyses=_ans)
#     d.configure_traits()
#     # print info.result
#     # if info.result:
#     # s = g.get_selection()
#     # for si in s:
#     # print si, si.analysis_type
