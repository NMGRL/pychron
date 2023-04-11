# ===============================================================================
# Copyright 2011 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================


# =============enthought library imports=======================

from chaco.scatterplot import ScatterPlot
from numpy import Inf
from traits.api import Bool, on_trait_change, Event, Int

# =============local library imports  ==========================
from pychron.graph.graph import Graph


# =============standard library imports ========================


class StackedGraph(Graph):
    """ """

    # indices=List

    bind_index = Bool(True)
    bind_padding = Bool(True)
    bind_y_title_spacing = Bool(True)
    bind_grids = Bool(True)
    equi_stack = True
    panel_height = 100
    _has_title = False
    # padding_bottom = 40
    fixed_bounds = Bool(False)

    metadata_updated = Event
    vertical_resize = Bool(True)

    def get_rescale_actions(self):
        return [("Rescale All Y", "rescale_all_y", {})]

    def rescale_all_y(self):
        ymi = Inf
        yma = -Inf
        for plot in self.plots:
            yma = max(yma, plot.value_range.high)
            ymi = min(ymi, plot.value_range.low)

        for i, plot in enumerate(self.plots):
            self.set_y_limits(ymi, yma, plotid=i)
        self.refresh()

    @on_trait_change("plots:value_axis:title_spacing")
    def _update_value_axis(self, obj, name, old, new):
        if self.bind_y_title_spacing:
            for p in self.plots:
                p.value_axis.trait_set(**{name: new})

    @on_trait_change("plots:[x_grid:[visible,line_+], y_grid:[visible,line_+]]")
    def _update_grids(self, obj, name, old, new):
        if self.bind_grids:
            grid = "x_grid" if obj.orientation == "vertical" else "y_grid"
            for p in self.plots:
                setattr(getattr(p, grid), name, new)
                # getattr(p, grid).visible = new

    @on_trait_change("plots:[padding_left, padding_right]")
    def _update_padding(self, obj, name, old, new):
        if self.bind_padding:
            for p in self.plots:
                p.trait_set(**{name: new})

    def clear_has_title(self):
        self._has_title = False

    def add_minor_xticks(self, plotid=0, **kw):
        if plotid != 0:
            kw["aux_component"] = self.plots[0]

        super(StackedGraph, self).add_minor_xticks(plotid=plotid, **kw)

    def add_minor_yticks(self, plotid=0, **kw):
        if plotid != 0:
            kw["aux_component"] = self.plots[0]

        super(StackedGraph, self).add_minor_yticks(plotid=plotid, **kw)

    def container_factory(self, *args, **kw):
        c = super(StackedGraph, self).container_factory(*args, **kw)
        """
            bind to self.plotcontainer.bounds
            allows stacked graph to resize vertically
        """
        c.on_trait_change(self._bounds_changed, "bounds")
        return c

    def new_plot(self, **kw):
        if "title" in kw:
            if self._has_title:
                kw.pop("title")
            self._has_title = True

        n = len(self.plotcontainer.components)
        # if n > 0:
        if "resizable" not in kw:
            kw["resizable"] = "h"
        # kw['resizable'] = 'h'
        if "bounds" not in kw:
            # kw["bounds"] = (1, self.panel_height)
            kw["resizable"] = kw.get("resizable", "hv")

        p = super(StackedGraph, self).new_plot(**kw)
        # p.value_axis.ensure_labels_bounded = True
        # p.value_axis.title_spacing = 50

        if n >= 1:
            pm = self.plotcontainer.components[0]
            pind = pm.index_range
            for pi in self.plotcontainer.components[1:]:
                pi.index_range = pind

        self.set_paddings()
        self._bounds_changed(self.plotcontainer.bounds)

        return p

    def set_paddings(self):
        pc = self.plotcontainer
        n = len(pc.components)
        bottom = pc.stack_order == "bottom_to_top"
        comps = pc.components
        if not bottom:
            comps = reversed(comps)
        if n > 1:
            for i, pi in enumerate(comps):
                if i < n - 1:
                    pi.padding_top = 0

                if i == 0:
                    pi.index_axis.visible = True
                else:
                    pi.index_axis.visible = False
                    pi.padding_bottom = 0

    def new_series(self, *args, **kw):
        s, _p = super(StackedGraph, self).new_series(*args, **kw)
        if self.bind_index:
            bind_id = kw.get("bind_id")
            if isinstance(s, ScatterPlot):
                s.bind_id = bind_id
                self._bind_index(s, bind_id=bind_id)

        return s, _p

    def _bounds_changed(self, bounds):
        """
        vertically resizes the stacked graph.
        the plots are sized equally
        """
        if self.vertical_resize:
            self._update_bounds(bounds, self.plotcontainer.components)

    def _update_bounds(self, bounds, comps):
        if self.fixed_bounds:
            return

        padding_top = sum([getattr(p, "padding_top") for p in comps])
        padding_bottom = sum([getattr(p, "padding_bottom") for p in comps])
        #
        pt = (
            self.plotcontainer.padding_top
            + self.plotcontainer.padding_bottom
            + padding_top
            + padding_bottom
        )
        n = len(self.plotcontainer.components)
        if self.equi_stack:
            for p in self.plotcontainer.components:
                p.bounds[1] = (bounds[1] - pt) / n
        else:
            try:
                self.plots[0].bounds[1] = (bounds[1] - pt) / max(1, (n - 1))
            except IndexError:
                pass

    def _update_metadata(self, bind_id, obj, name, old, new):
        if obj:
            if hasattr(obj, "suppress_update") and obj.suppress_update:
                return
            elif hasattr(obj, "suppress_hover_update") and obj.suppress_hover_update:
                return

        obj.suppress_update = True
        for plot in self.plots:
            for k, ps in plot.plots.items():
                si = ps[0]

                if si.index is not obj:
                    if hasattr(si, "bind_id"):
                        if si.bind_id is not None and si.bind_id == bind_id:
                            si.index.suppress_update = True
                            si.index.metadata = obj.metadata
                            si.index.suppress_update = False
        obj.suppress_update = False

    def _bind_index(self, scatter, bind_id=0, bind_selection=True, **kw):
        if bind_selection:

            def func(obj, name, old, new):
                self._update_metadata(bind_id, obj, name, old, new)

            scatter.index.on_trait_change(func, "metadata_changed")


class ColumnStackedGraph(StackedGraph):
    ncols = Int
    nrows = Int

    def _update_bounds(self, bounds, comps):
        padding_top = sum([getattr(p, "padding_top") for p in comps])
        padding_bottom = sum([getattr(p, "padding_bottom") for p in comps])
        pt = padding_bottom + padding_top

        n = self.nrows
        if self.equi_stack:
            for p in self.plotcontainer.components:
                p.bounds = (1, (bounds[1] - pt) / n)

        else:
            try:
                self.plots[0].bounds[1] = (bounds[1] - pt) / max(1, (n - 1))
            except IndexError:
                pass

    def set_paddings(self):
        pc = self.plotcontainer
        n = self.nrows
        comps = pc.components

        def colsplit(l, ncols):
            nn = len(l)
            return [l[i:nn:ncols] for i in range(ncols)]

        cols = colsplit(comps, self.ncols)

        if n > 1:
            for col in cols:
                n = len(col)
                for i, pi in enumerate(col):
                    pi.padding_top = 0
                    pi.padding_bottom = 0

                    if i == n - 1:
                        pi.index_axis.visible = True
                    else:
                        pi.index_axis.visible = False

    def container_factory(self, *args, **kw):
        kw["kind"] = "g"
        kw["shape"] = (self.nrows, self.ncols)

        # kw['spacing'] = (0, 0)
        c = super(ColumnStackedGraph, self).container_factory(*args, **kw)
        return c


if __name__ == "__main__":
    g = StackedGraph(
        resizable=True,
        fixed_bounds=True,
        container_dict={"padding_top": 15 * 4, "spacing": 10, "padding_bottom": 40},
    )
    for i in range(3):
        p = g.new_plot(padding=[80, 10, 10, 40], resizable="", bounds=(100, 100))
        p.fill_padding = True
        p.bgcolor = "green"
        # p=g.new_plot()
        g.new_series([1, 2, 3], [4, 5, 10 * i])
    g.configure_traits()
# ============= EOF ====================================
