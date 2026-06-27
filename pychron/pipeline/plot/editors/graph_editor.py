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

import logging
import os

from chaco.api import PlotLabel
from enable.component_editor import ComponentEditor as EnableComponentEditor
from traits.api import Any, Bool, Event, Property, cached_property
from traitsui.api import View, UItem

from pychron.core.helpers.iterfuncs import groupby_group_id
from pychron.pipeline.plot.editors.base_editor import BaseEditor
from pychron.pipeline.plot.figure_container import FigureContainer

logger = logging.getLogger(__name__)


class WarningLabel(PlotLabel):
    _in_layout = False

    def _font_changed(self, *args, **kw):
        # Suppress the chaco PlotLabel font-changed handler while a layout
        # pass is already running on this instance. The base handler calls
        # do_layout -> _layout_as_overlay which writes self.x/self.y and
        # triggers a position items-event; that fans out into more font/
        # layout observers and the cascade hits Python's recursion limit
        # inside traits._change_accepted (the TraitKind enum descriptor
        # bug under Py 3.12). Gating at the entrance kills the cycle
        # before it builds frames.
        if self._in_layout:
            return
        return super(WarningLabel, self)._font_changed(*args, **kw)

    def _layout_as_overlay(self, size=None, force=False):
        # Setting self.x / self.y writes through to position[0]/[1], which
        # fires a TraitListObject items-event.  Chaco listens to that, marks
        # the component dirty, and ultimately re-enters _layout_as_overlay
        # via a font/layout observer chain - infinite recursion on Apple
        # Silicon (the limit was previously absorbed silently on Intel via
        # late-bound dispatch).
        #
        # The equality short-circuit below is necessary but not sufficient:
        # parent layout can shift the component by sub-pixel amounts each
        # cycle, so self.x == nx never holds and the cascade still hits
        # the recursion limit (RecursionError seen in pychron.current.log
        # at 09:09:48).  A hard re-entry guard breaks the cycle
        # unconditionally.
        if self._in_layout or self.component is None:
            return
        nx = self.component.x + self.component.width / 2
        ny = self.component.y + self.component.height / 2
        if self.x == nx and self.y == ny:
            return
        self._in_layout = True
        try:
            self.x = nx
            self.y = ny
        finally:
            self._in_layout = False


class GraphEditor(BaseEditor):
    refresh_needed = Event
    save_needed = Event
    component = Property(depends_on="refresh_needed")
    basename = ""
    figure_model = Any
    figure_container = Any
    _force_refresh = Bool(False)

    @property
    def analyses(self):
        return self.items

    def save_file(self, path, force_layout=True, dest_box=None):
        _, tail = os.path.splitext(path)
        if tail not in (".pdf", ".png"):
            path = "{}.pdf".format(path)

        c = self.component

        """
            chaco becomes less responsive after saving if
            use_backbuffer is false and using pdf
        """
        from reportlab.lib.pagesizes import letter

        c.do_layout(size=letter, force=force_layout)

        _, tail = os.path.splitext(path)
        if tail == ".pdf":
            from pychron.core.pdf.save_pdf_dialog import myPdfPlotGraphicsContext

            gc = myPdfPlotGraphicsContext(filename=path, dest_box=dest_box)
            gc.render_component(c, valign="center")
            gc.save()

        else:
            from chaco.plot_graphics_context import PlotGraphicsContext

            gc = PlotGraphicsContext((int(c.outer_width), int(c.outer_height)))
            gc.render_component(c)
            gc.save(path)

    def set_items(
        self, ans, is_append: bool = False, refresh: bool = False, compress: bool = True
    ) -> None:
        if is_append:
            self.items.extend(ans)
        else:
            self.items = ans

        if self.items:
            self._set_name()
            if compress:
                self._compress_groups()
            if refresh:
                self.request_refresh()

    def request_refresh(self, force: bool = False) -> None:
        self._force_refresh = force
        self.refresh_needed = True

    def request_rebuild(self) -> None:
        self.request_refresh(force=True)

    def consume_refresh_request(self) -> bool:
        force = self._force_refresh
        self._force_refresh = False
        return force

    def _compress_groups(self):
        ans = self.items
        if ans:
            for i, (gid, analyses) in enumerate(groupby_group_id(ans)):
                for ai in analyses:
                    ai.group_id = i

    @cached_property
    def _get_component(self):
        comp = None
        if self.items:
            try:
                comp = self._component_factory()
            except Exception:
                # Previously raised a warning_dialog modal here, but on macOS
                # the dialog opens on the main thread while the recursive
                # chaco/trait-observer chain that produced the exception is
                # still firing on the same thread, leaving the modal painted
                # but unresponsive (beachball).  The fallback
                # _no_component_factory() below still runs and the user can
                # check the log for the traceback.
                logger.exception("Failed building pipeline figure component")
                self.warning(
                    "Failed to make figure (see log for traceback). "
                    "Falling back to empty component."
                )

        if comp is None:
            comp = self._no_component_factory()

        return comp

    def _component_factory(self):
        raise NotImplementedError

    def recalculate(self, model):
        pass

    def _get_component_hook(self, *args, **kw):
        pass

    def _no_component_factory(self):
        container = self.figure_container
        if not container:
            container = FigureContainer()
            self.figure_container = container

        component = self.figure_container.component
        w = WarningLabel(text="No Analyses", font="Helvetica 36", component=component)
        component.overlays.append(w)

        return component

    def _component_factory(self):
        raise NotImplementedError

    def get_component_view(self):
        return UItem("component", style="custom", editor=EnableComponentEditor())

    def traits_view(self):
        v = View(self.get_component_view(), resizable=True)
        return v


# ============= EOF =============================================
