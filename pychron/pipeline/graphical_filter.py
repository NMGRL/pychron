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
import math
from datetime import timedelta

from chaco.abstract_overlay import AbstractOverlay
from chaco.scales.api import CalendarScaleSystem
from chaco.scales_tick_generator import ScalesTickGenerator
from chaco.tools.broadcaster import BroadcasterTool
from enable.tools.drag_tool import DragTool
from numpy import array, where
from traits.api import HasTraits, Instance, List, Int, Bool, on_trait_change, Button, Str, Any, Float, Event
from traitsui.api import View, Controller, UItem, HGroup, VGroup, Item, spring

from pychron.core.helpers.iterfuncs import groupby_key
from pychron.experiment.utilities.identifier import ANALYSIS_MAPPING_INTS
from pychron.graph.graph import Graph
from pychron.graph.tools.analysis_inspector import AnalysisPointInspector
from pychron.graph.tools.point_inspector import PointInspectorOverlay
from pychron.graph.tools.rect_selection_tool import RectSelectionTool, RectSelectionOverlay
from pychron.pychron_constants import BLANK_TYPES

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
        counts = {k.lower(): float(len(list(v))) for k, v in groupby_key(analyses, 'analysis_type')}

    __cache__ = {}

    def f(x):
        x = x.lower()
        c = 0
        if offset:
            if x in __cache__:
                c = __cache__[x] + 1
            __cache__[x] = c
            c /= counts[x]

        return ANALYSIS_MAPPING_INTS[x] + c if x in ANALYSIS_MAPPING_INTS else -1

    return f


class GroupingTool(DragTool):
    dividers = List
    threshold = 2

    selected_divider = None
    grouping_event = Event

    def is_draggable(self, x, y):
        threshold = self.threshold
        comp = self.component
        y2 = comp.y2 + 5
        self.selected_divider = None
        for i, (dx, d) in enumerate(self.dividers):
            if abs(d - x) < threshold:
                if y2 + 6 >= y >= y2:
                    self.selected_divider = i
                    return True

    def dragging(self, event):
        self.dividers[self.selected_divider] = self._get_divider(event)
        self.component.invalidate_and_redraw()
        self.grouping_event = True

    def drag_cancel(self, event):
        self.drag_end(event)

    def normal_right_down(self, event):
        comp = self.component
        if comp.y2 + 6 > event.y > comp.y2:
            cdx, cx = self._get_divider(event)
            for i, (dx, x) in enumerate(self.dividers):
                if abs(cx - x) < self.threshold:
                    self.dividers.pop(i)
                    comp.invalidate_and_redraw()
                    event.handled = True
                    break

    def normal_left_down(self, event):
        if event.y > self.component.y2:
            cdx, cx = self._get_divider(event)
            for dx, x in self.dividers:
                if abs(cx - x) <= self.threshold:
                    break
            else:
                self.dividers.append((cdx, cx))
                self.grouping_event = True
                self.component.invalidate_and_redraw()

    def _get_divider(self, event):
        x = event.x
        dx = self.component.index_mapper.map_data(x)
        return dx, x


class GroupingOverlay(AbstractOverlay):
    def overlay(self, other_component, gc, view_bounds=None, mode="normal"):
        for dx, d in self.tool.dividers:
            gc.move_to(d, other_component.y)
            gc.line_to(d, other_component.y2 + 5)
            gc.rect(d - 3, other_component.y2 + 5, 6, 6)
            gc.draw_path()


class SelectionGraph(Graph):
    scatter = None
    grouping_tool = None

    def setup(self, x, y, ans):
        from pychron.pipeline.plot.plotter.ticks import StaticTickGenerator

        def display_atype(a):
            args = a.analysis_type.split('_')
            return ' '.join([a.capitalize() for a in args])

        atypes = list({display_atype(a) for a in ans})

        p = self.new_plot()
        p.padding_left = 90

        def tickformatter(x):
            return atypes[int(x)]

        p.y_axis.tick_label_rotate_angle = 60
        p.y_axis.tick_label_formatter = tickformatter
        p.y_axis.tick_generator = StaticTickGenerator(_nticks=len(atypes))
        p.y_axis.title = 'Analysis Type'
        p.y_axis.title_font = 'modern 18'
        p.y_axis.tick_label_font = 'modern 14'

        self.add_axis_tool(p, p.x_axis)
        self.add_axis_tool(p, p.y_axis)
        self.add_limit_tool(p, 'x')
        self.add_limit_tool(p, 'y')

        self.set_y_limits(min_=-1, max_=len(atypes))

        p.index_range.tight_bounds = False
        p.x_axis.tick_generator = ScalesTickGenerator(scale=CalendarScaleSystem())
        p.x_grid.tick_generator = p.x_axis.tick_generator
        p.x_axis.title = 'Time'
        p.x_axis.title_font = 'modern 18'
        p.x_axis.tick_label_font = 'modern 14'

        t = GroupingTool(component=p)
        p.tools.append(t)
        o = GroupingOverlay(component=p, tool=t)
        p.overlays.append(o)

        self.grouping_tool = t

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

        broadcaster.tools.append(rect_tool)
        broadcaster.tools.append(point_inspector)

        # range_selector = RangeSelection(scatter, left_button_selects=True)
        # broadcaster.tools.append(range_selector)

        # scatter.overlays.append(RangeSelectionOverlay(component=scatter))
        scatter.overlays.append(pinspector_overlay)
        scatter.overlays.append(rect_overlay)

        self.scatter = scatter


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

    mass_spectrometer = Str
    extract_device = Str
    gid = Int

    # is_append = True
    # use_all = False

    def setup(self, set_atypes=True):
        self.graph.clear()

        f = analysis_type_func(self.analyses, offset=self.use_offset_analyses)
        # ans = self._filter_projects(self.analyses)

        ans = self.analyses
        if set_atypes:
            def ff(at):
                # return ' '.join(map(str.capitalize, at.split('_')))
                return ' '.join((ai.capitalize() for ai in at.split('_')))

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
            ans = sorted(ans, key=lambda x: x.timestampf)
            self.analyses = ans
            # todo: CalendarScaleSystem off by 1 hour. add 3600 as a temp hack
            x, y = list(zip(*[(ai.timestampf + 3600, f(ai.analysis_type)) for ai in ans]))
            # x, y = zip(*[(ai.timestamp, f(ai.analysis_type)) for ai in ans])
        else:
            x, y, ans = [], [], []

        self.graph.setup(x, y, ans)

    def get_filtered_selection(self):
        selection = self.graph.scatter.index.metadata['selections']
        ans = self.analyses
        # unks = [ai for ai in self.analyses if ai.analysis_type == 'unknown']
        if selection:
            # unks = [ai for i, ai in enumerate(unks) if i not in selection]
            ans = [ai for i, ai in enumerate(self.analyses) if i not in selection]

        refs = self._filter_analysis_types(ans)
        self._calculate_groups(refs)
        # self._calculate_groups(unks)
        # return unks, refs
        return refs

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
                                               mass_spectrometers=[self.mass_spectrometer],
                                               extract_devices=[self.extract_device],
                                               exclude=uuids)
            func()
            if records:
                self.analyses.extend(records)
                self.setup()
                break

    def _calculate_groups(self, ans):
        px = None
        ts = array([ai.timestampf for ai in ans])
        i = -1
        for i, (dx, x) in enumerate(self.graph.grouping_tool.dividers):
            # convert to idx
            idx = where(ts < dx)[0][-1] + 1
            if i == 0:
                l, h = (0, idx)
            else:
                l, h = (px, idx)

            for ai in ans[l:h]:
                ai.group_id = int('{}{:02n}'.format(self.gid, i))

            px = idx

        for ai in ans[px:]:
            ai.group_id = int('{}{:02n}'.format(self.gid, i + 1))

    def _filter_analysis_types(self, ans):
        """
            only use analyses with analysis_type in self.analyses_types
        """
        ats = [x.lower().replace(' ', '_') for x in self.analysis_types]
        if 'blank' in ats:
            ats.extend(BLANK_TYPES)

        ans = [a for a in ans if a.analysis_type.lower() in ats]
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
    accept_button = Button('Accept')

    is_append = False
    # append_button = Button('Append')
    # replace_button = Button('Replace')
    help_str = Str('Select the analyses you want to EXCLUDE')

    search_backward = Button
    search_forward = Button

    def controller_search_backward_changed(self, info):
        self.model.search_backward()

    def controller_search_forward_changed(self, info):
        self.model.search_forward()

    # def controller_append_button_changed(self, info):
    #     self.is_append = True
    #     self.info.ui.dispose(result=True)
    #
    # def controller_replace_button_changed(self, info):
    #     self.is_append = False
    #     self.info.ui.dispose(result=True)

    def controller_accept_button_changed(self, info):
        self.info.ui.dispose(result=True)

    def traits_view(self):
        # egrp = HGroup(UItem('use_project_exclusion'),
        #               Item('exclusion_pad',
        #                    enabled_when='use_project_exclusion')),
        # bgrp = HGroup(spring, UItem('controller.append_button'), UItem('controller.replace_button'))

        ctrl_grp = VGroup(HGroup(Item('use_offset_analyses', label='Use Offset')))

        bgrp = HGroup(spring, UItem('controller.accept_button'))
        tgrp = HGroup(UItem('controller.help_str', style='readonly'), show_border=True)
        sgrp = HGroup(UItem('controller.search_backward'),
                      spring,
                      UItem('controller.search_forward'))
        ggrp = VGroup(sgrp, UItem('graph', style='custom'))
        v = View(VGroup(tgrp,
                        HGroup(ctrl_grp, ggrp),
                        bgrp),
                 title='Graphical Filter',
                 kind='livemodal',
                 resizable=True)
        return v

# ============= EOF =============================================
