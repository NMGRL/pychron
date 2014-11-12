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

#============= enthought library imports =======================
from traits.api import Property, Instance, Any, on_trait_change, Str
from traits.trait_types import DelegatesTo
from traitsui.api import View, UItem, InstanceEditor
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.base_editor import BaseTraitsEditor
from pychron.processing.analyses.changes import AnalysisRecord


class RecallEditor(BaseTraitsEditor):
    model = Any
    analysis_view = Instance('pychron.processing.analyses.analysis_view.AnalysisView')

    manager = Any

    name = Str('None')
    basename = Str
    instance_id = 0

    @on_trait_change('analysis_view:history_view:load_ages_needed')
    def handle_load_ages(self, obj):
        left, right = obj

        oid = self.model.selected_blanks_id

        self.manager.apply_blank_history(self.model, left.id)
        left.age = self.model.uage.nominal_value

        self.manager.apply_blank_history(self.model, right.id)
        right.age = self.model.uage.nominal_value

        self.manager.apply_blank_history(self.model, oid)

        # meas_analysis=db.get_analysis_uuid(self.model.uuid)
        # orig = meas_analysis.selected_histories.selected_blanks_id
        # meas_analysis.selected_histories.selected_blanks_id = orig
        # self.model.sync_blanks(meas_analysis)

    @on_trait_change('analysis_view:history_view:blank_selected_:selected')
    def handle_load_analyses(self, obj):
        db = self.manager.db
        with db.session_ctx():
            dbblank = db.get_blank(obj.id)
            obj.analyses = [AnalysisRecord(id=ai.analysis.id,
                                           record_id=ai.analysis.record_id) for ai in dbblank.analysis_set]

    @on_trait_change('analysis_view:history_view:apply_blank_change_needed')
    def handle_apply_blank_change(self, obj):

        apply_to_session, obj = obj
        if apply_to_session:
            self.manager.apply_session_blank_history(self.model, obj.id)
        else:
            self.manager.apply_blank_history(self.model,
                                             obj.id)

    @on_trait_change('analysis_view:main_view:show_iso_evo_needed')
    def handle_show_iso_evo(self, obj):
        from pychron.graph.stacked_regression_graph import StackedRegressionGraph

        self.manager.load_raw_data(self.model)

        g = StackedRegressionGraph()
        for ni in obj[::-1]:
            iso = next((i for i in self.model.isotopes.itervalues() if i.name == ni.name), None)
            g.new_plot(padding=[60, 10, 10, 40])
            g.new_series(iso.xs, iso.ys,
                         fit=iso.fit,
                         filter_outliers_dict=iso.filter_outliers_dict)
            g.set_x_limits(min_=0, max_=iso.xs[-1] * 1.1)
            g.set_x_title('Time (s)')
            g.set_y_title(iso.name)

        g.refresh()
        g.window_title = '{} {}'.format(self.name, ','.join([i.name for i in obj]))
        self.manager.application.open_view(g)

    def set_items(self, item):
        # if self.analysis_view:
        #     self.analysis_view.history_view.on_trait_change(self.handle_load_ages,
        #                                                     'load_ages_needed', remove=True)
        #     # self.analysis_view.history_view.on_trait_change('', '', remove=True)

        if isinstance(item, (tuple, list)):
            item = item[0]

        self.model = item
        self.analysis_view = self.model.analysis_view

        # self.analysis_view.history_view.on_trait_change(self.handle_load_ages, 'load_ages_needed')

        #set name
        r = self.analysis_view.analysis_id
        if self.instance_id:
            r = '{} #{}'.format(r, self.instance_id + 1)

        self.name = r

        #set basename
        self.basename = self.analysis_view.analysis_id

    def traits_view(self):
        v = View(UItem('editor.analysis_view',
                       style='custom',
                       editor=InstanceEditor()))
        return v

    # def _get_name(self):
    #     #if self.model and self.model.analysis_view:
    #     if self.analysis_view:
    #         r = self.analysis_view.analysis_id
    #         if self.instance_id:
    #             r = '{} #{}'.format(r, self.instance_id + 1)
    #         return r
    #     else:
    #         return 'None'
    #
    # def _get_basename(self):
    #     if self.analysis_view:
    #         return self.analysis_view.analysis_id
    #     else:
    #         return 'None'

#============= EOF =============================================
