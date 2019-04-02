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

from traits.api import Any, List

from pychron.pipeline.plot.editors.graph_editor import GraphEditor
from pychron.pipeline.plot.figure_container import FigureContainer


class FigureEditor(GraphEditor):
    references = List
    # save_required = Bool
    # table_editor = Any
    # component = Any
    # plotter_options_manager = Any
    # associated_editors = List
    plotter_options = Any
    # tool = Any

    # annotation_tool = Any

    # analysis_groups = List

    # tag = Event
    # save_db_figure = Event
    # invalid = Event
    #
    # saved_figure_id = Int
    # titles = List
    #
    # update_graph_on_set_items = True
    #
    # show_caption = False
    # caption_path = None
    # caption_text = None
    # @on_trait_change('plotter_options:save_required')
    # def handle_save_required(self):
    #     self.save_required = True
    def get_analysis_groups(self):
        ags = []
        for p in self.figure_model.panels:
            for pp in p.figures:
                ag = pp.analysis_group
                group = pp.options.get_group(pp.group_id)
                color = group.color
                ag.color = color
                ags.append(ag)
        return ags

    def enable_aux_plots(self):
        po = self.plotter_options
        for ap in po.aux_plots:
            ap.enabled = True

    def clear_aux_plot_limits(self):
        po = self.plotter_options
        if hasattr(po, 'aux_plots'):
            for ap in po.aux_plots:
                ap.clear_ylimits()
                ap.clear_xlimits()

    def set_items(self, *args, **kw):
        self.clear_aux_plot_limits()
        super(FigureEditor, self).set_items(*args, **kw)

    def force_update(self, force=False):
        model = self._figure_model_factory()
        model.refresh(force=force)

    def _component_factory(self):
        model = self._figure_model_factory()

        if not self.figure_container:
            self.figure_container = FigureContainer()
        #
        omodel = self.figure_container.model
        self.figure_container.model = model
        if model == omodel:
            self.figure_container.model_changed()

        self._get_component_hook(model)

        return self.figure_container.component

    def _figure_model_factory(self):
        model = self.figure_model
        if model is None:
            model = self.figure_model_klass()
            self.figure_model = model

        model.trait_set(plot_options=self.plotter_options,
                        # analysis_groups=self.analysis_groups,
                        # titles=self.titles,
                        analyses=self.items,
                        references=self.references)

        return model

    # def _component_factory(self):
    #     model = self._figure_model_factory()

        # container = self.figure_container
        # if not container:
        #     container = FigureContainer()
        #     self.figure_container = container
        #
        # container.model = model
        # # container.refresh()
        # return container.component

# ============= EOF =============================================
