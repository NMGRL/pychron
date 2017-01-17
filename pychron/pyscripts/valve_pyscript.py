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
import time

from traits.api import Any

from pychron.globals import globalv
from pychron.pychron_constants import NULL_STR
from pychron.pyscripts.pyscript import PyScript, verbose_skip, makeRegistry, \
    makeNamedRegistry

ELPROTOCOL = 'pychron.extraction_line.extraction_line_manager.ExtractionLineManager'

command_register = makeRegistry()
named_register = makeNamedRegistry(command_register)


class ValvePyScript(PyScript):
    runner = Any
    allow_lock = False
    retry_actuation = True

    def get_command_register(self):
        return command_register.commands.items()

    def gosub(self, *args, **kw):
        kw['runner'] = self.runner
        s = super(ValvePyScript, self).gosub(*args, **kw)
        if s:
            s.runner = None
        return s

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
        # if description is None:
        #     description = NULL_STR

        self.console_info('opening name={} desc={}'.format(name or NULL_STR, description or NULL_STR))

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

        self.console_info('closing name={} desc={}'.format(name or NULL_STR, description or NULL_STR))
        result = self._manager_action([('close_valve', (name,), dict(
            mode='script',
            description=description))], protocol=ELPROTOCOL)

        self.debug('---------------------------------------- close {} ({}) result={}'.format(name, description, result))
        if result is not None:
            self._finish_valve_change('close', result, name, description)

    @verbose_skip
    @command_register
    def is_open(self, name=None, description=''):
        self.console_info('is name={} desc={} open?'.format(name or NULL_STR, description or NULL_STR))
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
    def _finish_valve_change(self, action, result, name, description, retry=True):
        ok, changed = result[0]
        if changed:
            time.sleep(0.25)

        locked = self._manager_action([('get_software_lock', (name,), dict(
            mode='script',
            description=description))], protocol=ELPROTOCOL)

        # if action == 'close':
            # ok = not ok

        self.debug('action={}, ok={}, locked={}'.format(action, ok, locked))
        if not ok and not locked[0]:
            msg = 'Failed to {} valve Name="{}", Description="{}"'.format(action, name or '', description or '')
            self.console_info(msg)

            cancel = True
            if self.retry_actuation and retry:
                result = self._manager_action([('{}_valve'.format(action), (name,), dict(
                    mode='script',
                    description=description))], protocol=ELPROTOCOL)
                if result is not None:
                    cancel = not self._finish_valve_change(action, result, name, description, retry=False)

            if cancel:
                if not globalv.experiment_debug:
                    self.warning_dialog(msg)
                    self.cancel()
                else:
                   self.debug('Experiment debug mode. not canceling')
        else:
            return True

    def _get_valve_state(self, name, description):
        return self._manager_action([('get_valve_state', (name,), dict(
            description=description))], protocol=ELPROTOCOL)

# ============= EOF =============================================
