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

from traits.api import Float, Str, List, Property, cached_property, Button, Bool
from traitsui.api import Item, EnumEditor, UItem
from traitsui.editors.check_list_editor import CheckListEditor

from pychron.experiment.utilities.identifier import SPECIAL_MAPPING
from pychron.pipeline.editors.flux_results_editor import FluxPosition
from pychron.pipeline.graphical_filter import GraphicalFilterModel, GraphicalFilterView
from pychron.pipeline.nodes.data import DVCNode


class FindNode(DVCNode):
    pass


class BaseFindFluxNode(FindNode):
    irradiation = Str
    irradiations = Property

    levels = Property(depends_on='irradiation')

    def load(self, nodedict):
        self.irradiation = nodedict.get('irradiation', '')
        self._load_hook(nodedict)

    def _load_hook(self, nodedict):
        pass

    @cached_property
    def _get_levels(self):
        if self.irradiation:
            irrad = self.dvc.get_irradiation(self.irradiation)
            return sorted([l.name for l in irrad.levels])
        else:
            return []

    @cached_property
    def _get_irradiations(self):
        irrads = self.dvc.get_irradiations()
        return [i.name for i in irrads]


class FindVerticalFluxNode(BaseFindFluxNode):
    select_all_button = Button('Select All')
    selected_levels = List

    def run(self, state):
        state.levels = self.selected_levels
        state.irradiation = self.irradiation

    def _select_all_button_fired(self):
        self.selected_levels = self.levels

    def traits_view(self):
        v = self._view_factory(Item('irradiation', editor=EnumEditor(name='irradiations')),
                               UItem('select_all_button'),
                               UItem('selected_levels',
                                     style='custom',
                                     editor=CheckListEditor(name='levels')),
                               width=300,
                               title='Select Irradiation and Level',
                               resizable=True)
        return v


class FindFluxMonitorsNode(BaseFindFluxNode):
    name = 'Find Flux Monitors'

    # monitor_sample_name = Str('BW-2014-3')
    monitor_sample_name = Str('FC-2')

    level = Str
    use_browser = Bool(False)

    def run(self, state):
        if not self.irradiation or not self.level:
            self.configure()

        if not self.irradiation or not self.level:
            state.veto = self
        else:
            dvc = self.dvc
            state.geometry = dvc.get_irradiation_geometry(self.irradiation, self.level)

            ips = dvc.get_unknown_positions(self.irradiation, self.level, self.monitor_sample_name)

            state.unknown_positions = [self._fp_factory(state.geometry, self.irradiation, self.level,
                                                        ip.identifier, ip.sample.name, ip.position,
                                                        ip.j, ip.j_err) for ip in ips if ip.identifier]

            if self.use_browser:
                is_append, monitors = self.get_browser_analyses(irradiation=self.irradiation,
                                                                level=self.level)
            else:
                ans = dvc.get_flux_monitor_analyses(self.irradiation, self.level, self.monitor_sample_name)
                ans = [aii for ai in ans for aii in ai.record_views]
                monitors = self.dvc.make_analyses(ans)

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

    def _load_hook(self, nodedict):
        self.level = nodedict.get('level', '')

    def traits_view(self):
        v = self._view_factory(Item('irradiation', editor=EnumEditor(name='irradiations')),
                               Item('level', editor=EnumEditor(name='levels')),
                               Item('use_browser'),
                               width=300,
                               title='Select Irradiation and Level')
        return v


class FindReferencesNode(FindNode):
    user_choice = False
    threshold = Float

    analysis_type = Str
    analysis_types = List

    extract_device = Str
    # enable_extract_device = Bool
    extract_devices = List

    mass_spectrometer = Str
    # enable_mass_spectrometer = Bool
    mass_spectrometers = List
    # analysis_type_name = None
    name = 'Find References'

    def reset(self):
        self.user_choice = None
        super(FindReferencesNode, self).reset()

    def load(self, nodedict):
        self.threshold = nodedict['threshold']
        self.analysis_type = nodedict['analysis_type']

    def finish_load(self):
        self.extract_devices = self.dvc.get_extraction_device_names()
        self.mass_spectrometers = self.dvc.get_mass_spectrometer_names()

    # def dump(self, obj):
    #     obj['threshold'] = self.threshold

    def _analysis_type_changed(self, new):
        if new == 'Blank Unknown':
            new = 'Blank'
        self.name = 'Find {}s'.format(new)

    def pre_run(self, state, configure=True):
        if not state.unknowns:
            return

        eds = {ai.extract_device for ai in state.unknowns}
        self.enable_extract_device = len(eds) > 1
        self.extract_device = list(eds)[0]

        ms = {ai.mass_spectrometer for ai in state.unknowns}
        self.enable_mass_spectrometer = len(ms) > 1
        self.mass_spectrometer = list(ms)[0]

        return super(FindReferencesNode, self).pre_run(state, configure=configure)

    def run(self, state):

        key = lambda x: x.group_id
        for gid, ans in groupby(sorted(state.unknowns, key=key), key=key):
            if self._run_group(state, gid, list(ans)):
                return

        self._compress_groups(state.unknowns)
        self._compress_groups(state.references)

    def _compress_groups(self, ans):
        if not ans:
            return

        key = lambda x: x.group_id
        ans = sorted(ans, key=key)
        groups = groupby(ans, key)

        for i, (gid, analyses) in enumerate(groups):
            for ai in analyses:
                ai.group_id = i

    def _run_group(self, state, gid, unknowns):
        times = sorted((ai.timestamp for ai in unknowns))

        atype = self.analysis_type.lower().replace(' ', '_')
        refs = self.dvc.find_references(times, atype, hours=self.threshold,
                                        extract_device=self.extract_device,
                                        mass_spectrometer=self.mass_spectrometer,
                                        make_records=False)

        if refs:
            unknowns.extend(refs)
            model = GraphicalFilterModel(analyses=unknowns,
                                         dvc=self.dvc,
                                         low_post=times[0],
                                         high_post=times[-1],
                                         threshold=self.threshold,
                                         gid=gid)

            model.setup()
            model.analysis_types = [self.analysis_type]

            obj = GraphicalFilterView(model=model)
            info = obj.edit_traits(kind='livemodal')
            if info.result:
                unks, refs = model.get_filtered_selection()

                refs = self.dvc.make_analyses(refs)
                if obj.is_append:
                    state.append_references = True
                    state.references.extend(refs)
                else:
                    state.append_references = False
                    state.references = list(refs)

                if unks is not None:
                    state.unknowns = unks
                state.has_references = True
            else:
                state.veto = self
                return True

    def traits_view(self):
        v = self._view_factory(Item('threshold',
                                    tooltip='Maximum difference between blank and unknowns in hours',
                                    label='Threshold (Hrs)'),
                               Item('analysis_type',
                                    label='Analysis Type',
                                    editor=EnumEditor(name='analysis_types')),

                               Item('extract_device', editor=EnumEditor(name='extract_devices'),
                                    label='Extract Device'),
                               Item('mass_spectrometer',
                                    label='Mass Spectrometer',
                                    editor=EnumEditor(name='mass_spectrometers')))

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
