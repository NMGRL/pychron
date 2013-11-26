#===============================================================================
# Copyright 2013 Jake Ross
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
#===============================================================================

#============= enthought library imports =======================
from pychron.pyscripts.extraction_line_pyscript import ExtractionPyScript
from pychron.pyscripts.pyscript import verbose_skip, makeRegistry
from pychron.lasers.laser_managers.ilaser_manager import ILaserManager
#============= standard library imports ========================
#============= local library imports  ==========================
command_register = makeRegistry()


class UVExtractionPyScript(ExtractionPyScript):

    def get_command_register(self):
        cm = super(UVExtractionPyScript, self).get_command_register()
        return command_register.commands.items() + cm

    def set_default_context(self):
        super(UVExtractionPyScript, self).set_default_context()
        self.setup_context(reprate=0,
                           mask=0,
                           attenuator=0)

    @property
    def reprate(self):
        return self.get_context()['reprate']

    @verbose_skip
    @command_register
    def set_reprate(self, value=''):
        if value=='':
            value=self.reprate

        self._manager_action([('set_reprate', (value,), {})],
                             protocol=ILaserManager,
                             name=self.extract_device)


    @verbose_skip
    @command_register
    def drill_point(self, value='', name=''):
        if name == '':
            name = self.position

        if value == '':
            value = self.extract_value

        self._manager_action([('drill_point', (value, name,), {})],
                             protocol=ILaserManager,
                             name=self.extract_device)

    @verbose_skip
    @command_register
    def trace_path(self, name='', value='', kind='continuous'):
        if name == '':
            name = self.position

        if value == '':
            value = self.extract_value

        self._manager_action([('trace_path', (value, name, kind), {})],
                             protocol=ILaserManager,
                             name=self.extract_device)

    @verbose_skip
    @command_register
    def extract(self, power='', units='', position=None):
        if not position is None:
            self.move_to_position(position)

            if position.startswith('l'):
                self.trace_path(power, position)
            elif position.startswith('s'):
                self.trace_path(power, position, kind='step')
            elif position.startswith('d'):
                self.drill_point(power, position)
            else:
                super(UVExtractionPyScript, self).extract(power=power, units=units)

        else:
            super(UVExtractionPyScript, self).extract(power=power, units=units)

#============= EOF =============================================
