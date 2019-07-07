# ===============================================================================
# Copyright 2018 ross
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
from traits.api import Instance, Bool, Str, List, Float
from traitsui.api import UItem, VGroup, Item, HGroup, EnumEditor

from pychron.core.helpers.iterfuncs import groupby_key
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.experiment.script.script import Script
from pychron.loggable import Loggable

ATTRS = ('pattern', 'duration', 'cleanup', 'extract_value', 'beam_diameter', 'ramp_duration')


class BulkRunFixer(Loggable):
    """
    used by ExperimentEditor when it validates its queue before saving
    """
    extraction_script = Instance(Script, ())
    measurement_script = Instance(Script, ())
    post_measurement_script = Instance(Script, ())
    post_equilibration_script = Instance(Script, ())

    extraction_script_enabled = Bool
    measurement_script_enabled = Bool

    unknown_enabled = Bool
    patterns = List
    pattern = Str
    enabled_pattern = Bool

    extract_value = Float
    enabled_extract_value = Bool
    cleanup = Float
    enabled_cleanup = Bool

    duration = Float
    enabled_duration = Bool
    beam_diameter = Float
    enabled_beam_diameter = Bool
    ramp_duration = Float
    enabled_ramp_duration = Bool
    title = Str

    def fix(self, runs):
        if not self.confirmation_dialog('Would you like to run the Bulk Run Fixer?'):
            return

        for atype, ris in groupby_key(runs, 'analysis_type'):
            ris = list(ris)
            self.unknown_enabled = atype == 'unknown'
            es, ms = zip(*[(r.extraction_script, r.measurement_script) for r in ris])
            es, ms = list(set(es)), list(set(ms))
            # es,ms = zip(*list({r.extraction_script for r in ris}))

            self.extraction_script_enabled = len(es) > 1
            self.extraction_script.name = es[0]

            self.measurement_script_enabled = len(ms) > 1
            self.measurement_script.name = ms[0]

            if self.unknown_enabled:
                for attr in ATTRS:

                    ats = list({getattr(r, attr) for r in ris})
                    if len(ats) > 1:
                        setattr(self, attr, ats[0])
                        setattr(self, 'enabled_{}'.format(attr), True)
                    else:
                        setattr(self, 'enabled_{}'.format(attr), False)

            self.title = atype.capitalize()
            info = self.edit_traits()
            if info.result:
                self._apply(ris)
            else:
                break

    def _apply(self, ris):
        for r in ris:
            for tag in ('extraction', 'measurement'):
                tag = '{}_script'.format(tag)
                if getattr(self, '{}_enabled'.format(tag)):
                    setattr(r, tag, getattr(self, tag))

            if self.unknown_enabled:
                for attr in ATTRS:
                    if attr == 'extract_value' and r.aliquot:
                        continue

                    if getattr('enabled_{}'.format(attr)):
                        setattr(r, attr, getattr(self, attr))

    def traits_view(self):
        script_grp = VGroup(HGroup(UItem('extraction_script_enabled', label='Enabled'),
                                   UItem('extraction_script', style='custom',
                                         enabled_when='extraction_script_enabled')),

                            HGroup(UItem('measurement_script_enabled', label='Enabled'),
                                   UItem('measurement_script', style='custom',
                                         enabled_when='measurement_script_enabled')),
                            # UItem('post_equilibration_script', style='custom'),
                            # UItem('post_measurement_script', style='custom')
                            label='Script',
                            show_border=True
                            )
        unk_grp = VGroup(HGroup(UItem('enabled_pattern'), Item('pattern', editor=EnumEditor(name='patterns'))),
                         HGroup(UItem('enabled_extract_value'), Item('extract_value', label='Extract')),
                         HGroup(UItem('enabled_duration'), Item('duration')),
                         HGroup(UItem('enabled_cleanup'), Item('cleanup')),
                         HGroup(UItem('enabled_beam_diameter'), Item('beam_diameter')),
                         HGroup(UItem('enabled_ramp_duration'), Item('ramp_duration')),
                         visible_when='unknown_enabled',
                         show_border=True,
                         label='Unknown')
        v = okcancel_view(VGroup(unk_grp,
                                 script_grp),
                          title=self.title)
        return v

    def _measurement_script_default(self):
        s = Script(label='measurement')
        return s

    def _extraction_script_default(self):
        s = Script(label='extraction')
        return s


if __name__ == '__main__':
    from pychron.paths import paths

    paths.build('~/PychronDev')
    af = BulkRunFixer()


    class Run:
        extraction_script = 'Foo'
        measurement_script = 'Bar'
        analysis_type = 'unknown'


    a = Run()
    a.analysis_type = 'air'
    b = Run()
    b.analysis_type = 'blank'
    c = Run()
    runs = [a, b, c]
    af.auto_fix(runs)
# ============= EOF =============================================
