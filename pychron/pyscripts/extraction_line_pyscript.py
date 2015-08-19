# ===============================================================================
# Copyright 2011 Jake Ross
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
# ===============================================================================

# ============= enthought library imports =======================

from traits.api import List
# ============= standard library imports ========================
import time
import inspect
import re
# ============= local library imports  ==========================
from pychron.core.ramper import Ramper
from pychron.external_pipette.protocol import IPipetteManager
from pychron.hardware.core.exceptions import TimeoutError
from pychron.hardware.core.i_core_device import ICoreDevice
from pychron.pyscripts.pyscript import verbose_skip, makeRegistry
from pychron.lasers.laser_managers.ilaser_manager import ILaserManager
from pychron.pyscripts.valve_pyscript import ValvePyScript
from pychron.pychron_constants import EXTRACTION_COLOR, LINE_STR

# ELPROTOCOL = 'pychron.extraction_line.extraction_line_manager.ExtractionLineManager'

COMPRE = re.compile(r'[A-Za-z]*')

# make a registry to hold all the commands exposed by ExtractionPyScript
# used when building the context
# see PyScript.get_context and get_command_register
command_register = makeRegistry()


class RecordingCTX(object):
    def __init__(self, script, name):
        self._script = script
        self._name = name

    def __enter__(self, *args, **kw):
        self._script.start_video_recording(self._name)

    def __exit__(self, *args, **kw):
        self._script.stop_video_recording()


class ExtractionPyScript(ValvePyScript):
    """
    The ExtractionPyScript is used to program the extraction and gettering of
    sample gas.
    """
    _resource_flag = None
    info_color = EXTRACTION_COLOR
    snapshots = List

    _extraction_positions = List

    def set_run_identifier(self, v):
        self.setup_context(run_identifier=v)

    def get_extraction_positions(self, clear=True):
        """
        Returns a list of x,y,z tuples
        each tuple represents where the extraction occurred

        if clear is True (default) ``self._extraction_positions`` set to an empty list

        :return: list of x,y,z tuples
        :rtype: list of tuples

        """
        ret = self._extraction_positions
        if clear:
            self._extraction_positions = []

        return ret

    def get_response_blob(self):
        """
        Get the extraction device's response blob

        :return: response blob. binary string representing time v measured output
        :rtype: str
        """
        return self._extraction_action([('get_response_blob', (), {})])

    def get_output_blob(self):
        """
        Get the extraction device's output blob

        :return: output blob: binary string representing time v requested output
        :rtype: str
        """
        return self._extraction_action([('get_output_blob', (), {})])

    def output_achieved(self):
        """
        Return a formated string with the extraction "heating" results::

            Requested Output= 100.000
            Achieved Output= 99.012

        :return: Formatted string with results
        :rtype: str
        """
        request = self.extract
        ach = self._extraction_action([('get_achieved_output', (), {})])
        try:
            request = float(request)
        except (ValueError, TypeError):
            request = 0

        try:
            ach = float(ach)
        except (ValueError, TypeError):
            ach = 0

        return ('Requested Output= {:0.3f}'.format(request),
                'Achieved Output=  {:0.3f}'.format(ach))

    def get_command_register(self):
        cm = super(ExtractionPyScript, self).get_command_register()
        return command_register.commands.items() + cm

    def set_default_context(self):
        """
        provide default values for all the properties exposed in the script
        """

        self.setup_context(analysis_type='',
                           position='',
                           pattern='',
                           extract_device='',
                           extract_value=0,
                           extract_units='',
                           tray='',
                           ramp_rate='',
                           duration=0,
                           cleanup=0,
                           beam_diameter=None,
                           run_identifier='default_runid')

    # ===============================================================================
    # commands
    # ===============================================================================
    @verbose_skip
    @command_register
    def wake(self):
        self._extraction_action('wake')
        self._manager_action('wake')

    @verbose_skip
    @command_register
    def waitfor(self, func_or_tuple, start_message='', end_message='',
                check_period=1, timeout=0):
        """

        tuple format: (device_name, function_name, comparison)
        comparison ::

          x<10
          10<x<20

        callable can of form ``func() or func(ti) or func(ti, i)``
        where ``ti`` is the current relative time (relative to start of waitfor) and ``i`` is a counter

        :param func_or_tuple: wait for function to return True
        :type func_or_tuple: callable, tuple
        :param start_message: Message to display at start
        :type start_message: str
        :param end_message: Message to display at end
        :type end_message: str
        :param check_period: Delay between checks in seconds
        :type check_period: int, float
        :param timeout: Cancel waiting after ``timeout`` seconds
        :type timeout: int, float
        """
        include_time = False
        include_time_and_count = False
        if isinstance(func_or_tuple, tuple):
            func = self._make_waitfor_func(*func_or_tuple)
        else:
            func = func_or_tuple
            args = inspect.getargspec(func).args
            if len(args) == 1:
                include_time = True
            elif len(args) == 2:
                include_time_and_count = True

        if not func:
            self.debug('no waitfor function')
            self.cancel()

        self.console_info('waitfor started. {}'.format(start_message))
        st = time.time()
        i = 0
        while 1:
            if self.is_canceled():
                self.console_info('waitfor canceled')
                return

            ct = time.time() - st
            if timeout and ct > timeout:
                self.warning('waitfor timed out after {}s'.format(timeout))
                self.cancel()
                return

            if include_time:
                args = (ct,)
            elif include_time_and_count:
                args = (ct, i)
                i += 1
            else:
                args = tuple()

            if func(*args):
                self.console_info('waitfor ended. {}'.format(end_message))
                break

            time.sleep(check_period)

    @verbose_skip
    @command_register
    def power_map(self, cx, cy, padding, bd, power):
        pass

    @verbose_skip
    @command_register
    def degas(self, lumens=0, duration=0):
        self._extraction_action([('do_machine_vision_degas', (lumens, duration), {})])

    @verbose_skip
    @command_register
    def autofocus(self, set_zoom=True):
        self._extraction_action([('do_autofocus', (), {'set_zoom': set_zoom})])

    @verbose_skip
    @command_register
    def set_light(self, value=''):
        self._extraction_action([('set_light', (value,), {})])

    @verbose_skip
    @command_register
    def snapshot(self, name='', prefix='', view_snapshot=False, pic_format='.jpg'):
        """
            if name not specified use RID_Position e.g 12345-01A_3
        """
        if not name:
            pos = '_'.join(self.position)
            name = '{}_{}'.format(self.run_identifier, pos)

        name = '{}{}'.format(prefix, name)
        ps = self._extraction_action([('take_snapshot', (name, pic_format),
                                       {'view_snapshot':view_snapshot})])
        if ps:
            self.snapshots.append(ps)

    @command_register
    def video_recording(self, name='video'):
        return RecordingCTX(self, name)

    @verbose_skip
    @command_register
    def start_video_recording(self, name='video'):
        self._extraction_action([('start_video_recording', (), {'name': name})])

    @verbose_skip
    @command_register
    def stop_video_recording(self):
        self._extraction_action([('stop_video_recording', (), {})])

    @verbose_skip
    @command_register
    def set_x(self, value, velocity=''):
        self._set_axis('x', value, velocity)

    @verbose_skip
    @command_register
    def set_y(self, value, velocity=''):
        self._set_axis('y', value, velocity)

    @verbose_skip
    @command_register
    def set_z(self, value, velocity=''):
        self._set_axis('z', value, velocity)

    @verbose_skip
    @command_register
    def set_xy(self, value, velocity=''):
        self._set_axis('xy', value, velocity)

    @verbose_skip
    @command_register
    def set_motor_lock(self, name='', value=''):
        if name and value is not '':
            l = 'YES' if value else 'NO'
            self.console_info('set motor lock to {}'.format(name, l))
            self._extraction_action([('set_motor_lock', (name, value), {})])

    @verbose_skip
    @command_register
    def set_motor(self, name='', value=''):
        self.console_info('setting motor "{}" to {}'.format(name, value))
        if name is not '' and value is not '':
            if value is not None:
                self._extraction_action([('set_motor', (name, value), {})])

    @verbose_skip
    @command_register
    def get_value(self, name):
        try:
            print name, self.get_context()[name]
            return self.get_context()[name]
        except KeyError:
            self.warning('no name {} in context'.format(name))
            pass

    @verbose_skip
    @command_register
    def move_to_position(self, position='', autocenter=False):
        if position == '':
            position = self.position

        if position:
            position_ok = True
            if isinstance(position, (list, tuple)):
                position_ok = all(position)
        else:
            position_ok = False

        if position_ok:
            self.console_info('{} move to position {}'.format(self.extract_device,
                                                      position))
            success = self._extraction_action([('move_to_position',
                                                (position, autocenter), {})])

            if not success:
                self.info('{} move to position failed'.format(self.extract_device))
                self.cancel()
            else:
                self.console_info('move to position suceeded')
                return True
        else:
            self.console_info('move not required. position is None')
            return True

    @verbose_skip
    @command_register
    def execute_pattern(self, pattern='', block=True):
        if pattern == '':
            pattern = self.pattern

        st = time.time()
        # set block=True to wait for pattern completion
        self._extraction_action([('execute_pattern', (pattern,), {'block': block})])

        return time.time() - st

    @verbose_skip
    @command_register
    def set_tray(self, tray=''):
        if tray == '':
            tray = self.tray

        self.console_info('set tray to {}'.format(tray))
        result = self._extraction_action([('set_stage_map', (tray,), {})])
        return result

    @verbose_skip
    @command_register
    def load_pipette(self, identifier, timeout=300):
        """
            this is a non blocking command. it simply sends a command to apis to
            start one of its runscripts.

            it is the ExtractionPyScripts responsiblity to handle the waiting.
            use the waitfor command to wait for signals from apis.
        """
        from pychron.external_pipette.apis_manager import InvalidPipetteError
        cmd = 'load_blank_non_blocking' if self.analysis_type == 'blank' else 'load_pipette_non_blocking'
        try:
            #bug _manager_action only with except tuple of len 1 for args
            rets = self._extraction_action([(cmd, (identifier,),
                                             # {'timeout': timeout, 'script': self})],
                                             {'timeout': timeout, })],
                                           name='externalpipette',
                                           protocol=IPipetteManager)

            return rets[0]
        except InvalidPipetteError, e:
            self.cancel(protocol=IPipetteManager)
            e = str(e)
            self.warning(e)
            return e

    @verbose_skip
    @command_register
    def extract_pipette(self, identifier='', timeout=300):
        """
            this is an atomic command. use the apis_controller config file to define
            the isolation procedures.
        """
        from pychron.external_pipette.apis_manager import InvalidPipetteError
        if identifier == '':
            identifier = self.extract_value

        cmd = 'load_blank' if self.analysis_type == 'blank' else 'load_pipette'
        try:
            #bug _manager_action only with except tuple of len 1 for args
            rets = self._extraction_action([(cmd, (identifier,),
                                             {'timeout': timeout, 'script': self})],
                                           name='externalpipette',
                                           protocol=IPipetteManager)

            return rets[0]
        except (TimeoutError, InvalidPipetteError), e:
            self.cancel(protocol=IPipetteManager)
            e = str(e)
            self.warning(e)
            return e

    @verbose_skip
    @command_register
    def extract(self, power='', units=''):
        if power == '':
            power = self.extract_value
        if units == '':
            units = self.extract_units

        ed = self.extract_device
        ed = ed.replace('_', ' ')

        # get current position and add as an extraction position
        pos = self._extraction_action([('get_position', (), {})])
        self._extraction_positions.append(pos)

        # set an experiment message
        if self.manager:
            self.manager.set_extract_state('{} ON! {}({})'.format(ed, power, units), color='red')

        self.console_info('extract sample to {} ({})'.format(power, units))
        self._extraction_action([('extract', (power,), {'units': units})])

    @verbose_skip
    @command_register
    def end_extract(self):
        self._extraction_action([('end_extract', (), {})])

    @verbose_skip
    @command_register
    def ramp(self, start=0, setpoint=0, duration=0, rate=0, period=1):
        self.debug('ramp parameters start={}, '
                   'setpoint={}, duration={}, rate={}, period={}'.format(start, setpoint, duration, rate, period))
        def func(i, ramp_step):
            if self._cancel:
                return

            self.console_info('ramp step {}. setpoint={}'.format(i, ramp_step))
            if not self._extraction_action([('set_laser_power', (ramp_step,), {})]):
                return

            if self._cancel:
                return

            return True

        st = time.time()
        rmp = Ramper()
        rmp.ramp(func, start, setpoint, duration, rate, period)
        return time.time() - st

    @verbose_skip
    @command_register
    def acquire(self, name=None, clear=False):
        if self.runner is None:
            self.debug('+++++++++++++++++++++++ Runner is None')
            return

        self.console_info('acquire {}'.format(name))
        self.runner.connect()

        r = self.runner.get_resource(name)

        if not clear:
            if r.isSet():
                self.console_info('waiting for access')

                if self.manager:
                    self.manager.set_extract_state('Waiting for Resource Access. "{}"'.format(name), color='red')

                while r.isSet():
                    if self._cancel:
                        break
                    self._sleep(1)

                    if not self.runner.reset_connection():
                        self.cancel()
                        break

        if not self._cancel:
            self._resource_flag = r
            r.set()
            self.console_info('{} acquired'.format(name))

        if self.manager:
            self.manager.set_extract_state(False)

    @verbose_skip
    @command_register
    def wait(self, name=None, criterion=0):
        if self.runner is None:
            self.debug('+++++++++++++++++++++++ Runner is None')
            return

        self.console_info('waiting for {} = {}'.format(name, criterion))
        r = self.runner.get_resource(name)

        cnt = 0
        resp = r.read()
        if resp is not None:
            while resp != criterion:
                time.sleep(1)

                # only verbose every 10s
                resp = r.read(verbose=cnt % 10 == 0)
                if resp is None:
                    continue

                cnt += 1
                if cnt > 100:
                    cnt = 0

        self.console_info('finished waiting')

    @verbose_skip
    @command_register
    def release(self, name=None):
        self.console_info('release {}'.format(name))
        if self.runner is None:
            self.debug('+++++++++++++++++++++++ Runner is None')
            return

        r = self.runner.get_resource(name)
        if r is not None:
            r.clear()
        else:
            self.console_info('Could not release {}'.format(name))

    @verbose_skip
    @command_register
    def set_resource(self, name=None, value=1):
        if self.runner is None:
            self.debug('+++++++++++++++++++++++ Runner is None')
            return

        r = self.runner.get_resource(name)
        if r is not None:
            r.set(value)
        else:
            self.console_info('Could not set {}'.format(name))

    @verbose_skip
    @command_register
    def get_resource_value(self, name=None):
        if self.runner is None:
            self.debug('+++++++++++++++++++++++ Runner is None')
            return

        r = self.runner.get_resource(name)
        resp = None
        if r is not None:
            if hasattr(r, 'get'):
                resp = r.get()
            else:
                resp = r.isSet()
        else:
            self.console_info('Could not get {}'.format(name))

        self.debug('Get Resource Value {}={}'.format(name, resp))
        return resp

    @verbose_skip
    @command_register
    def enable(self):
        ed = self.extract_device
        ed = ed.replace('_', ' ')
        self.manager.set_extract_state('{} Enabled'.format(ed))

        return self._manager_action([('enable_device', (), {})],
                                    protocol=ILaserManager,
                                    name=self.extract_device)

    @verbose_skip
    @command_register
    def disable(self):
        return self._disable()

    @verbose_skip
    @command_register
    def prepare(self):
        return self._extraction_action([('prepare', (), {})])
    # ===============================================================================
    # properties
    # ===============================================================================
    def _get_property(self, key, default=None):
        ctx = self.get_context()
        return ctx.get(key, default)

    @property
    def duration(self):
        return self._get_property('duration')
        # return self.get_context()['duration']

    @property
    def cleanup(self):
        return self._get_property('cleanup')
        # return self.get_context()['cleanup']

    @property
    def pattern(self):
        return self._get_property('pattern')
        # return self.get_context()['pattern']

    @property
    def analysis_type(self):
        at = self._get_property('analysis_type')
        self.debug('getting analysis type for {}. '
                   'analysis_type={}'.format(self.run_identifier, at))
        return at
        # return self.get_context()['analysis_type']

    @property
    def extract_device(self):
        return self._get_property('extract_device')
        # return self.get_context()['extract_device']

    @property
    def tray(self):
        return self._get_property('tray')
        # return self.get_context()['tray']

    @property
    def position(self):
        """
            if position is 0 return None
        """
        # pos = self.get_context()['position']
        pos = self._get_property('position')
        if pos:
            return pos

    @property
    def extract_value(self):
        return self._get_property('extract_value')
        # return self.get_context()['extract_value']

    @property
    def extract_units(self):
        return self._get_property('extract_units')
        # return self.get_context()['extract_units']

    @property
    def beam_diameter(self):
        return self._get_property('beam_diameter')
        # return self.get_context()['beam_diameter']
    @property
    def run_identifier(self):
        return self._get_property('run_identifier')
    # ===============================================================================
    # private
    # ===============================================================================
    def _cancel_hook(self):
        self.disable()

    def _get_device(self, name):
        app = self._get_application()
        if app is not None:
            return app.get_service_by_name(ICoreDevice, name)
        else:
            self.warning('_get_device - No application')

    def _make_waitfor_func(self, name, funcname, comp):
        dev = self._get_device(name)
        if dev:
            devfunc = getattr(dev, funcname)
            m = COMPRE.findall(comp)
            if m:
                k = m[0]

                def func(*args):
                    return eval(comp, {k: devfunc()})

                return func
            else:
                self.warning('invalid comparison. valid e.g.=x<10 comp={}'.format(comp))
        else:
            self.warning('no device available named "{}"'.format(name))

    def _extraction_action(self, *args, **kw):
        if not 'name' in kw:
            kw['name'] = self.extract_device

        kw['name'] = kw.get('name', self.extract_device) or self.extract_device
        if kw['name'] in ('Extract Device', LINE_STR):
            return

        # if not 'protocol' in kw:
        #     kw['protocol'] = ILaserManager
        kw['protocol']=kw.get('protocol', ILaserManager) or ILaserManager

        return self._manager_action(*args, **kw)

    def _disable(self, protocol=None):
        self.debug('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% disable')
        if self.manager:
            self.manager.set_extract_state(False)

        return self._extraction_action([('disable_device', (), {})], protocol=protocol)

    def _set_axis(self, name, value, velocity):
        kw = dict(block=True)
        if velocity:
            kw['velocity'] = value

        success = self._extraction_action([('set_{}'.format(name), (value,), kw)])
        if not success:
            self.console_info('{} move to position failed'.format(self.extract_device))
        else:
            self.console_info('move to position suceeded')
        return True

    def _cancel_hook(self, **kw):
        if self._resource_flag:
            self._resource_flag.clear()

        # disable the extract device
        self._disable(**kw)

        # stop patterning
        self._stop_pattern(**kw)

    def _stop_pattern(self, protocol=None):
        self._extraction_action([('stop_pattern', (), {})], protocol=protocol)

# ============= EOF ====================================