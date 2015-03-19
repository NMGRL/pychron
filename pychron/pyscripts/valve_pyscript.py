# ===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Any
# ============= standard library imports ========================
import time
# ============= local library imports  ==========================
from pychron.globals import globalv
from pychron.pyscripts.pyscript import PyScript, verbose_skip, makeRegistry, \
    makeNamedRegistry

ELPROTOCOL = 'pychron.extraction_line.extraction_line_manager.ExtractionLineManager'

command_register = makeRegistry()
named_register = makeNamedRegistry(command_register)


class ValvePyScript(PyScript):
    runner = Any
    allow_lock = False

    def get_command_register(self):
        return command_register.commands.items()

    def gosub(self, *args, **kw):
        kw['runner'] = self.runner
        super(ValvePyScript, self).gosub(*args, **kw)

    @verbose_skip
    @command_register
    def lock(self, name=None, description=''):
        if description is None:
            description = '---'

        self.console_info('locking {} ({})'.format(name, description))
        if self.allow_lock:
            return self._manager_action([('lock_valve', (name,), dict(
                mode='script',
                description=description))], protocol=ELPROTOCOL)
        else:
            self.warning('Valve locking not enabled for this script')

    @verbose_skip
    @command_register
    def unlock(self, name=None, description=''):
        if description is None:
            description = '---'

        self.console_info('unlocking {} ({})'.format(name, description))
        if self.allow_lock:
            return self._manager_action([('unlock_valve', (name,), dict(
                mode='script',
                description=description))], protocol=ELPROTOCOL)
        else:
            self.warning('Valve locking not enabled for this script')

    @verbose_skip
    @named_register('open')
    def _m_open(self, name=None, description=''):
        st = time.time()
        if description is None:
            description = '---'

        self.console_info('opening {} ({})'.format(name, description))

        result = self._manager_action([('open_valve', (name,), dict(
            mode='script',
            description=description))], protocol=ELPROTOCOL)
        et = time.time() - st
        self.debug('---------------------------------------- open {} ({}) result={}, '
                   'time={:0.2f} sec'.format(name, description, result, et))
        if result is not None:
            self._finish_valve_change('open', result, name, description)

    @verbose_skip
    @command_register
    def close(self, name=None, description=''):

        if description is None:
            description = '---'

        self.console_info('closing {} ({})'.format(name, description))
        result = self._manager_action([('close_valve', (name,), dict(
            mode='script',
            description=description))], protocol=ELPROTOCOL)

        self.debug('---------------------------------------- close {} ({}) result={}'.format(name, description, result))
        if result is not None:
            self._finish_valve_change('close', result, name, description)

    @verbose_skip
    @command_register
    def is_open(self, name=None, description=''):
        self.console_info('is {} ({}) open?'.format(name, description))
        result = self._get_valve_state(name, description)
        if result:
            return result[0] is True

    @verbose_skip
    @command_register
    def is_closed(self, name=None, description=''):
        self.console_info('is {} ({}) closed?'.format(name, description))
        result = self._get_valve_state(name, description)
        if result:
            r = result[0] is False
            self.debug('is closed {}'.format(r))
            return r

    # private
    def _finish_valve_change(self, action, result, name, description):
        ok, changed = result[0]
        if changed:
            time.sleep(0.25)

        locked = self._manager_action([('get_software_lock', (name,), dict(
            mode='script',
            description=description))], protocol=ELPROTOCOL)
        if not ok and not locked:
            self.console_info('Failed to {} valve {} {}'.format(action, name, description))

            if not globalv.experiment_debug:
                self.cancel()
            else:
                self.debug('Experiment debug mode. not canceling')

    def _get_valve_state(self, name, description):
        return self._manager_action([('get_valve_state', (name,), dict(
            description=description))], protocol=ELPROTOCOL)

# ============= EOF =============================================
