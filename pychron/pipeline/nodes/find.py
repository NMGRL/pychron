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
from __future__ import absolute_import
from itertools import groupby

from traits.api import Float, Str, List, Property, cached_property, Button, Bool
from traitsui.api import Item, EnumEditor, UItem, VGroup, HGroup

from pychron.core.ui.check_list_editor import CheckListEditor
from pychron.experiment.utilities.identifier import SPECIAL_MAPPING
from pychron.pipeline.editors.flux_results_editor import FluxPosition
from pychron.pipeline.graphical_filter import GraphicalFilterModel, GraphicalFilterView
from pychron.pipeline.nodes.data import DVCNode
from pychron.pychron_constants import DEFAULT_MONITOR_NAME, NULL_STR
from six.moves import map


class FindNode(DVCNode):
    pass


class BaseFindFluxNode(FindNode):
    irradiation = Str
    irradiations = Property
    samples = Property(depends_on='irradiation, level')
    levels = Property(depends_on='irradiation')
    level = Str
    monitor_sample_name = Str(DEFAULT_MONITOR_NAME)

    def load(self, nodedict):
        self.irradiation = nodedict.get('irradiation', '')
        self._load_hook(nodedict)

    def _load_hook(self, nodedict):
        pass

    def _to_template(self, d):
        d['irradiation'] = self.irradiation

    @cached_property
    def _get_samples(self):
        if self.irradiation and self.level:
            return self.dvc.distinct_sample_names(self.irradiation, self.level)
        else:
            return []

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
    # monitor_sample_name = Str('FC-2')

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

    def _to_template(self, d):
        super(FindFluxMonitorsNode, self)._to_template(d)
        d['level'] = self.level

    def traits_view(self):
        v = self._view_factory(Item('irradiation', editor=EnumEditor(name='irradiations')),
                               Item('level', editor=EnumEditor(name='levels')),
                               Item('monitor_sample_name', editor=EnumEditor(name='samples')),
                               Item('use_browser'),
                               width=300,
                               title='Select Irradiation and Level')
        return v


class FindReferencesNode(FindNode):
    user_choice = False
    threshold = Float

    loadname = Str

    display_loads = Property(depends_on='limit_to_analysis_loads')
    loads = List
    analysis_loads = List
    limit_to_analysis_loads = Bool(True)

    analysis_types = List
    available_analysis_types = List

    extract_device = Str
    enable_extract_device = Bool
    extract_devices = List

    mass_spectrometer = Str
    enable_mass_spectrometer = Bool
    mass_spectrometers = List
    # analysis_type_name = None
    name = 'Find References'

    def reset(self):
        self.user_choice = None
        super(FindReferencesNode, self).reset()

    def load(self, nodedict):
        self.threshold = nodedict.get('threshold', 10)
        self.analysis_types = nodedict.get('analysis_types', [])
        if self.analysis_types:
            self.name = 'Find {}'.format(','.join(self.analysis_types))
        self.limit_to_analysis_loads = nodedict.get('limit_to_analysis_loads', True)

    def finish_load(self):
        self.extract_devices = self.dvc.get_extraction_device_names()
        self.mass_spectrometers = self.dvc.get_mass_spectrometer_names()
        names = [NULL_STR]
        dbnames = self.dvc.get_load_names()
        if dbnames:
            names += dbnames

        self.loads = names

    def _to_template(self, d):
        d['threshold'] = self.threshold
        d['analysis_types'] = self.analysis_types
        d['limit_to_analysis_loads'] = self.limit_to_analysis_loads

    # def _analysis_types_changed(self, new):
    #     if new == 'Blank Unknown':
    #         new = 'Blank'
    #     self.name = 'Find {}s'.format(new)

    def pre_run(self, state, configure=True):
        if not state.unknowns:
            return

        eds = {ai.extract_device for ai in state.unknowns}
        self.enable_extract_device = len(eds) > 1
        self.extract_device = list(eds)[0]

        ms = {ai.mass_spectrometer for ai in state.unknowns}
        self.enable_mass_spectrometer = len(ms) > 1
        self.mass_spectrometer = list(ms)[0]

        ls = {ai.loadname for ai in state.unknowns}
        self.analysis_loads = list(ls)

        self._pre_run_hook()
        return super(FindReferencesNode, self).pre_run(state, configure=configure)

    def run(self, state):
        key = lambda x: x.group_id
        for gid, ans in groupby(sorted(state.unknowns, key=key), key=key):
            if self._run_group(state, gid, list(ans)):
                return

        self._compress_groups(state.unknowns)
        self._compress_groups(state.references)

    def _pre_run_hook(self):
        pass

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
        atypes = [ai.lower().replace(' ', '_') for ai in self.analysis_types]
        kw = dict(extract_devices=self.extract_device,
                  mass_spectrometers=self.mass_spectrometer,
                  make_records=False)

        if self.loadname and self.loadname != NULL_STR:
            refs = self.dvc.find_references_by_load(self.loadname, atypes, **kw)
            if refs:
                times = sorted([ai.rundate for ai in refs])
        else:
            times = sorted([ai.rundate for ai in unknowns])
            refs = self.dvc.find_references(times, atypes, hours=self.threshold, **kw)

        if refs:
            unknowns.extend(refs)
            model = GraphicalFilterModel(analyses=unknowns,
                                         dvc=self.dvc,
                                         low_post=times[0],
                                         high_post=times[-1],
                                         threshold=self.threshold,
                                         gid=gid)

            model.setup()
            model.analysis_types = self.analysis_types  # [self.analysis_type]

            obj = GraphicalFilterView(model=model)
            info = obj.edit_traits(kind='livemodal')
            if info.result:
                refs = model.get_filtered_selection()
                refs = self.dvc.make_analyses(refs)
                if obj.is_append:
                    state.append_references = True
                    state.references.extend(refs)
                else:
                    state.append_references = False
                    state.references = list(refs)

                # if unks is not None:
                #     state.unknowns.extend( unks)
                state.has_references = True
            else:
                state.veto = self
                return True

    def traits_view(self):
        v = self._view_factory(HGroup(Item('loadname', editor=EnumEditor(name='display_loads')),
                                      Item('limit_to_analysis_loads', label='Analysis Loads')),
                               Item('threshold',
                                    tooltip='Maximum difference between blank and unknowns in hours',
                                    label='Threshold (Hrs)'),
                               VGroup(UItem('analysis_types',
                                            style='custom',
                                            editor=CheckListEditor(name='available_analysis_types', cols=3)),
                                      show_border=True, label='Analysis Types'),

                               Item('extract_device',
                                    enabled_when='enable_extract_device',
                                    editor=EnumEditor(name='extract_devices'),
                                    label='Extract Device'),
                               Item('mass_spectrometer',
                                    label='Mass Spectrometer',
                                    enabled_when='enable_mass_spectrometer',
                                    editor=EnumEditor(name='mass_spectrometers')))

        return v

    def _available_analysis_types_default(self):
        return sorted([' '.join(map(str.capitalize, k.split('_'))) for k in SPECIAL_MAPPING.keys()])

    def _get_display_loads(self):
        if self.limit_to_analysis_loads:
            return self.analysis_loads
        else:
            return self.loads
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
