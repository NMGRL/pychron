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
from pyface.confirmation_dialog import confirm
from pyface.constant import YES
from traits.api import Float, Str, List, Instance, Property, cached_property
from traitsui.api import Item, EnumEditor
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.confirmation import remember_confirmation_dialog
from pychron.experiment.utilities.identifier import SPECIAL_MAPPING
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
    flux_monitors = List

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
            state.has_flux_monitors = True
            state.irradiation = self.irradiation
            state.level = self.level

            if self.flux_monitors:
                #v = confirm(None, 'You already have Flux Monitors found. Do you want to refind the monitors')
                #print v, v != YES
                #if v != YES:
                if confirm(None, 'You already have Flux Monitors found. Do you want to refind the monitors') != YES:
                    state.flux_monitors = self.flux_monitors
                    return

            with dvc.session_ctx():
                ans = dvc.get_flux_monitor_analyses(self.irradiation, self.level, self.monitor_sample_name)
                monitors = self.dvc.make_analyses(ans, calculate_f_only=False)
                #dvc = self.dvc
            #with dvc.session_ctx():
            #    ans = dvc.get_flux_monitor_analyses(self.irradiation, self.level, self.monitor_sample_name)
            #    monitors = self.dvc.make_analyses(ans, calculate_f_only=False)
            #
            #state.geometry = dvc.get_irradiation_geometry(self.irradiation, self.level)
            state.flux_monitors = monitors
            self.flux_monitors = monitors
            print 'oooo', len(self.flux_monitors)


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

        times = sorted((ai.rundate for ai in state.unknowns))

        atype = self.analysis_type.lower().replace(' ', '_')
        refs = self.dvc.find_references(times, atype)
        # print 'refs', atype, refs
        if refs:
            review = self.user_choice
            if not self.user_choice:
                # ask if use wants to review
                review, remember = remember_confirmation_dialog('What you like to review this Node? '
                                                                '{}'.format(self.name))
                if remember:
                    self.user_choice = review

            if review:
                ans = state.unknowns[:]
                ans.extend(refs)
                # refs.extend(state.unknowns)
                model = GraphicalFilterModel(analyses=ans)
                model.setup()
                # print self.analysis_type
                # print model.available_analysis_types
                model.analysis_types = [self.analysis_type]

                obj = GraphicalFilterView(model=model)
                info = obj.edit_traits(kind='livemodal')
                if info.result:
                    refs = model.get_filtered_selection()

                    if obj.is_append:
                        state.references.extend(refs)
                    else:
                        state.references = list(refs)
            else:
                state.references = refs

            state.has_references = True

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
