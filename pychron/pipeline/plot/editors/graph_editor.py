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
import os
from itertools import groupby

from enable.component_editor import ComponentEditor as EnableComponentEditor
from traits.api import List, Property, Event, cached_property, Any
from traitsui.api import View, UItem

from pychron.envisage.tasks.base_editor import grouped_name, BaseTraitsEditor


class GraphEditor(BaseTraitsEditor):
    analyses = List
    refresh_needed = Event
    save_needed = Event
    component = Property(depends_on='refresh_needed')
    basename = ''
    figure_model = Any

    def save_file(self, path, force_layout=True, dest_box=None):
        _, tail = os.path.splitext(path)
        if tail not in ('.pdf', '.png'):
            path = '{}.pdf'.format(path)

        c = self.component

        '''
            chaco becomes less responsive after saving if
            use_backbuffer is false and using pdf
        '''
        from reportlab.lib.pagesizes import letter

        c.do_layout(size=letter, force=force_layout)

        _, tail = os.path.splitext(path)
        if tail == '.pdf':
            from chaco.pdf_graphics_context import PdfPlotGraphicsContext

            gc = PdfPlotGraphicsContext(filename=path,
                                        dest_box=dest_box)
            gc.render_component(c, valign='center')
            gc.save()

        else:
            from chaco.plot_graphics_context import PlotGraphicsContext

            gc = PlotGraphicsContext((int(c.outer_width), int(c.outer_height)))
            gc.render_component(c)
            gc.save(path)

            # self.rebuild_graph()

    def set_items(self, ans, is_append=False, refresh=False, compress=True):
        if is_append:
            self.analyses.extend(ans)
        else:
            self.analyses = ans

        if self.analyses:
            self._set_name()
            if compress:
                self._compress_groups()
            if refresh:
                self.refresh_needed = True

    def _set_name(self):
        na = list(set([ni.labnumber for ni in self.analyses]))
        na = grouped_name(na)
        self.name = '{} {}'.format(na, self.basename)

    def _compress_groups(self):
        ans = self.analyses
        if not ans:
            return

        key = lambda x: x.group_id
        ans = sorted(ans, key=key)
        groups = groupby(ans, key)
        # try:
        # mgid, analyses = groups.next()
        # except StopIteration:
        #     return

        # print 'compress groups'
        # for ai in analyses:
        # ai.group_id = 0

        for i, (gid, analyses) in enumerate(groups):
            for ai in analyses:
                # ai.group_id = gid - mgid
                ai.group_id = i

    @cached_property
    def _get_component(self):
        self.figure_model = None
        return self._component_factory()

    def _component_factory(self):
        raise NotImplementedError

    def traits_view(self):
        v = View(UItem('component',
                       style='custom',
                       width=650,
                       editor=EnableComponentEditor()),
                 resizable=True)
        return v

# ============= EOF =============================================
