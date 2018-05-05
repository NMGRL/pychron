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
from __future__ import absolute_import
import os
from itertools import groupby
from operator import attrgetter

from chaco.plot_label import PlotLabel
from enable.component_editor import ComponentEditor as EnableComponentEditor
from traits.api import List, Property, Event, cached_property, Any
from traitsui.api import View, UItem

from pychron.envisage.tasks.base_editor import grouped_name, BaseTraitsEditor
from pychron.pipeline.plot.figure_container import FigureContainer


class WarningLabel(PlotLabel):
    def _layout_as_overlay(self, size=None, force=False):
        self.x = self.component.x+self.component.width/2
        self.y = self.component.y+self.component.height/2


class GraphEditor(BaseTraitsEditor):
    analyses = List
    refresh_needed = Event
    save_needed = Event
    component = Property(depends_on='refresh_needed')
    basename = ''
    figure_model = Any
    figure_container = Any

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
            from pychron.core.pdf.save_pdf_dialog import myPdfPlotGraphicsContext

            gc = myPdfPlotGraphicsContext(filename=path,
                                          dest_box=dest_box)
            gc.render_component(c, valign='center')
            gc.save()

        else:
            from chaco.plot_graphics_context import PlotGraphicsContext

            gc = PlotGraphicsContext((int(c.outer_width), int(c.outer_height)))
            gc.render_component(c)
            gc.save(path)

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
        na = sorted(list(set([ni.identifier for ni in self.analyses])))
        na = grouped_name(na)
        self.name = '{} {}'.format(na, self.basename)

    def _compress_groups(self):
        ans = self.analyses
        if ans:
            key = attrgetter('group_id')
            ans = sorted(ans, key=key)
            groups = groupby(ans, key)

            for i, (gid, analyses) in enumerate(groups):
                for ai in analyses:
                    ai.group_id = i

    @cached_property
    def _get_component(self):
        if self.analyses:
            if self.figure_container:
                self.figure_container.model_changed(False)
            return self._component_factory()

        else:
            return self._no_component_factory()

    def _no_component_factory(self):
        container = self.figure_container
        if not container:
            container = FigureContainer()
            self.figure_container = container

        component = self.figure_container.component
        w = WarningLabel(text='No Analyses',
                         font='Helvetica 36',
                         component=component)
        component.overlays.append(w)

        return component

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
