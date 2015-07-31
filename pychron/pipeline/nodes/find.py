# ===============================================================================
# Copyright 2015 Jake Ross
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
from itertools import groupby

from traits.api import Float, Str, List, Instance, Property, cached_property
from traitsui.api import Item, EnumEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.experiment.utilities.identifier import SPECIAL_MAPPING
from pychron.pipeline.editors.flux_results_editor import FluxPosition
from pychron.pipeline.graphical_filter import GraphicalFilterModel, GraphicalFilterView
from pychron.pipeline.nodes.base import BaseNode


class FindNode(BaseNode):
    dvc = Instance('pychron.dvc.dvc.DVC')


class FindFluxMonitorsNode(FindNode):
    name = 'Find Flux Monitors'

    # monitor_sample_name = Str('BW-2014-3')
    monitor_sample_name = Str('FC-2')
    irradiation = Str
    irradiations = Property

    level = Str
    levels = Property(depends_on='irradiation')

    def load(self, nodedict):
        self.irradiation = nodedict.get('irradiation', '')
        self.level = nodedict.get('level', '')

    @cached_property
    def _get_levels(self):
        if self.irradiation:
            with self.dvc.session_ctx():
                irrad = self.dvc.get_irradiation(self.irradiation)
                return [l.name for l in irrad.levels]
        else:
            return []

    @cached_property
    def _get_irradiations(self):
        with self.dvc.session_ctx():
            irrads = self.dvc.get_irradiations()
            return [i.name for i in irrads]

    def traits_view(self):
        v = self._view_factory(Item('irradiation', editor=EnumEditor(name='irradiations')),
                               Item('level', editor=EnumEditor(name='levels')),
                               width=300,
                               title='Select Irradiation and Level')
        return v

    def run(self, state):
        if not self.irradiation or not self.level:
            self.configure()

        if not self.irradiation or not self.level:
            state.veto = self
        else:
            dvc = self.dvc
            state.geometry = dvc.get_irradiation_geometry(self.irradiation, self.level)

            with dvc.session_ctx():
                ips = dvc.get_unknown_positions(self.irradiation, self.level, self.monitor_sample_name)

                state.unknown_positions = [self._fp_factory(state.geometry, self.irradiation, self.level,
                                                            ip.identifier, ip.sample.name, ip.position,
                                                            ip.j, ip.j_err) for ip in ips]

                ans = dvc.get_flux_monitor_analyses(self.irradiation, self.level, self.monitor_sample_name)

                monitors = self.dvc.make_analyses(ans, calculate_f_only=False)

            state.unknowns = monitors
            state.flux_monitors = monitors
            state.has_flux_monitors = True
            state.irradiation = self.irradiation
            state.level = self.level

    def _fp_factory(self, geom, irradiation, level, identifier, sample, hole_id, j, j_err):
        x, y, r, idx = geom[hole_id - 1]
        fp = FluxPosition(identifier=identifier,
                          irradiation=irradiation,
                          level=level,
                          sample=sample, hole_id=hole_id,
                          saved_j=j or 0,
                          saved_jerr=j_err or 0,
                          # mean_j=nominal_value(mj),/
                          # mean_jerr=std_dev(mj),
                          x=x, y=y)
        return fp


class FindReferencesNode(FindNode):
    user_choice = False
    threshold = Float

    analysis_type = Str
    analysis_types = List
    # analysis_type_name = None
    name = 'Find References'

    def reset(self):
        self.user_choice = None

    def load(self, nodedict):
        self.threshold = nodedict['threshold']
        self.analysis_type = nodedict['analysis_type']

    # def dump(self, obj):
    #     obj['threshold'] = self.threshold

    def _analysis_type_changed(self, new):
        self.name = 'Find {}s'.format(new)

    def run(self, state):
        if not state.unknowns:
            return

        key = lambda x: x.group_id
        for gid, ans in groupby(sorted(state.unknowns, key=key), key=key):
            if self._run_group(state, gid, list(ans)):
                return

    def _run_group(self, state, gid, unknowns):
        times = sorted((ai.rundate for ai in unknowns))

        atype = self.analysis_type.lower().replace(' ', '_')
        refs = self.dvc.find_references(times, atype, hours=self.threshold)
        # print 'refs', atype, refs
        if refs:
            # ans = unknowns[:]
            unknowns.extend(refs)
            model = GraphicalFilterModel(analyses=unknowns,
                                         dvc=self.dvc,
                                         low_post=times[0],
                                         high_post=times[-1],
                                         threshold=self.threshold)
            model.setup()

            model.analysis_types = [self.analysis_type]

            obj = GraphicalFilterView(model=model)
            info = obj.edit_traits(kind='livemodal')
            if info.result:
                refs = model.get_filtered_selection()
                for ri in refs:
                    ri.group_id = gid

                if obj.is_append:
                    state.references.extend(refs)
                else:
                    state.references = list(refs)

                state.has_references = True
            else:
                state.veto = self
                return True

    def traits_view(self):
        v = self._view_factory(Item('threshold',
                                    tooltip='Maximum difference between blank and unknowns in hours',
                                    label='Threshold (Hrs)'),
                               Item('analysis_type',
                                    editor=EnumEditor(name='analysis_types')))

        return v

    def _analysis_types_default(self):
        return [' '.join(map(str.capitalize, k.split('_'))) for k in SPECIAL_MAPPING.keys()]

#
# class FindAirsNode(FindNode):
#     name = 'Find Airs'
#     analysis_type = 'blank_unknown'
#     analysis_type_name = 'Air'
#
#
# class FindBlanksNode(FindNode):
#     name = 'Find Blanks'
#     analysis_type = 'blank_unknown'
#     analysis_type_name = 'Blank Unknown'


# ============= EOF =============================================
