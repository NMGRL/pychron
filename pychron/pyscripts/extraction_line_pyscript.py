#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import List
#============= standard library imports ========================
import time
#============= local library imports  ==========================
from pychron.external_pipette.apis_manager import InvalidPipetteError
from pychron.external_pipette.protocol import IPipetteManager
from pychron.hardware.core.exceptions import TimeoutError
from pychron.pyscripts.pyscript import verbose_skip, makeRegistry
from pychron.lasers.laser_managers.ilaser_manager import ILaserManager
# from pychron.lasers.laser_managers.extraction_device import ILaserManager
from pychron.pyscripts.valve_pyscript import ValvePyScript
from pychron.pychron_constants import EXTRACTION_COLOR

ELPROTOCOL = 'pychron.extraction_line.extraction_line_manager.ExtractionLineManager'

'''
    make a registry to hold all the commands exposed by ExtractionPyScript
    used when building the context
    see PyScript.get_context and get_command_register
    
'''
command_register = makeRegistry()


class RecordingCTX(object):
    def __init__(self, script, name):
        self._script = script
        self._name = name

    def __enter__(self, *args, **kw):
        self._script.start_video_recording(self._name)

    def __exit__(self, *args, **kw):
        self._script.stop_video_recording()


class Ramper(object):
    def ramp(self, func, start, end, duration, rate=0, period=1):
        """
            rate = units/s
            duration= s

            use rate if specified
        """
        st = time.time()
        if end is not None:
            if rate:
                duration = abs(start - end) / float(rate)

            if duration:
                self._ramp(func, start, end, duration, period)

        return time.time() - st

    def _ramp(self, func, start, end, duration, period):
        st = time.time()
        i = 1

        step = period * (end - start) / float(duration)

        while (time.time() - st) < duration:
            ct = time.time()
            v = start + i * step
            if func(i, v):
                time.sleep(max(0, period - (time.time() - ct)))
                i += 1
            else:
                break


class ExtractionPyScript(ValvePyScript):
    _resource_flag = None
    info_color = EXTRACTION_COLOR
    snapshot_paths = List

    _extraction_positions = List

    def get_extraction_positions(self, clear=True):
        """
            return a list of x,y,z tuples
            each tuple represents where the extraction occurred
            if clear is True (default)
            _extraction_positions set to empty list
        """
        ret = self._extraction_positions
        if clear:
            self._extraction_positions = []

        return ret

    def get_response_blob(self):
        return self._extraction_action([('get_response_blob', (), {})])

    def get_output_blob(self):
        return self._extraction_action([('get_output_blob', (), {})])

    def output_achieved(self):
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

    #===============================================================================
    # commands
    #===============================================================================


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
    def snapshot(self, name=''):
        ps = self._extraction_action([('take_snapshot', (), {'name': name})])
        if ps:
            ps = ps[0]
            self.snapshot_paths.append(ps[1])

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
            self.info('set motor lock to {}'.format(name, l))
            self._extraction_action([('set_motor_lock', (name, value), {})])

    @verbose_skip
    @command_register
    def set_motor(self, name='', value=''):
        self.info('setting motor "{}" to {}'.format(name, value))
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
            self.info('{} move to position {}'.format(self.extract_device,
                                                      position))
            success = self._extraction_action([('move_to_position',
                                                (position, autocenter), {})])
            if not success:
                self.info('{} move to position failed'.format(self.extract_device))
            else:
                self.info('move to position suceeded')
                return True
        else:
            self.info('move not required. position is None')
            return True

    @verbose_skip
    @command_register
    def execute_pattern(self, pattern='', block=False):
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

        self.info('set tray to {}'.format(tray))
        result = self._extraction_action([('set_stage_map', (tray,), {})])
        return result

    @verbose_skip
    @command_register
    def extract_pipette(self, identifier='', timeout=300):

        if identifier == '':
            identifier = self.extract_value

        cmd = 'load_blank' if self.analysis_type == 'blank' else 'load_pipette'
        try:
            rets = self._extraction_action([(cmd, (self, identifier,),
                                             {'timeout': timeout})],
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

        #get current position and add as an extraction position
        pos = self._extraction_action([('get_position', (), {})])
        self._extraction_positions.append(pos)

        #set an experiment message
        self.manager.set_extract_state('{} ON! {}({})'.format(ed, power, units), color='red')

        self.info('extract sample to {} ({})'.format(power, units))
        self._extraction_action([('extract', (power,), {'units': units})])

    @verbose_skip
    @command_register
    def end_extract(self):
        self._extraction_action([('end_extract', (), {})])

    @verbose_skip
    @command_register
    def ramp(self, start=0, end=0, duration=0, rate=0, period=1):
        def func(i, ramp_step):
            if self._cancel:
                return

            self.info('ramp step {}. setpoint={}'.format(i, ramp_step))
            if not self._extraction_action([('set_laser_power', (ramp_step,), {})]):
                return

            if self._cancel:
                return

            return True

        st = time.time()
        rmp = Ramper()
        rmp.ramp(func, start, end, duration, rate, period)
        return time.time() - st

    @verbose_skip
    @command_register
    def acquire(self, name=None, clear=False):
        if self.runner is None:
            self.debug('+++++++++++++++++++++++ Runner is None')
            return

        self.info('acquire {}'.format(name))
        r = self.runner.get_resource(name)

        s = False
        if not clear:
            s = r.isSet()
            if s:
                self.info('waiting for access')

        while s:
            if self._cancel:
                break
            self._sleep(1)
            s = r.isSet()

        if not self._cancel:
            self._resource_flag = r
            r.set()
            self.info('{} acquired'.format(name))

    @verbose_skip
    @command_register
    def wait(self, name=None, criterion=0):
        if self.runner is None:
            self.debug('+++++++++++++++++++++++ Runner is None')
            return

        self.info('waiting for {} = {}'.format(name, criterion))
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

        self.info('finished waiting')

    @verbose_skip
    @command_register
    def release(self, name=None):
        self.info('release {}'.format(name))
        if self.runner is None:
            self.debug('+++++++++++++++++++++++ Runner is None')
            return

        r = self.runner.get_resource(name)
        if r is not None:
            r.clear()
        else:
            self.info('Could not release {}'.format(name))

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
            self.info('Could not set {}'.format(name))

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
            self.info('Could not get {}'.format(name))

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

    #===============================================================================
    # properties
    #===============================================================================
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
        return self._get_property('analysis_type')
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

    #===============================================================================
    # private
    #===============================================================================
    def _extraction_action(self, *args, **kw):
        if not 'name' in kw:
            kw['name'] = self.extract_device

        if not 'protocol' in kw:
            kw['protocol'] = ILaserManager

        return self._manager_action(*args, **kw)

    def _disable(self, protocol=None):
        self.debug('%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% disable')
        if self.manager:
            self.manager.set_extract_state(False)

        return self._manager_action([('disable_device', (), {})],
                                    protocol=ILaserManager,
                                    name=self.extract_device)

    def _set_axis(self, name, value, velocity):
        kw = dict(block=True)
        if velocity:
            kw['velocity'] = value

        success = self._extraction_action([('set_{}'.format(name), (value,), kw)])
        if not success:
            self.info('{} move to position failed'.format(self.extract_device))
        else:
            self.info('move to position suceeded')
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

#============= EOF ====================================

#    @verbose_skip
#    def _m_open(self, name=None, description=''):
#
#        if description is None:
#            description = '---'
#
#        self.info('opening {} ({})'.format(name, description))
#
#        self._manager_action([('open_valve', (name,), dict(
#                                                      mode='script',
#                                                      description=description
#                                                      ))], protocol=ELPROTOCOL)
#
#    @verbose_skip
#    def close(self, name=None, description=''):
#
#        if description is None:
#            description = '---'
#
#        self.info('closing {} ({})'.format(name, description))
#        self._manager_action([('close_valve', (name,), dict(
#                                                      mode='script',
#                                                      description=description
#                                                      ))], protocol=ELPROTOCOL)
#    def get_context(self):
#        d = super(ExtractionPyScript, self).get_context()

#        #=======================================================================
#        #Parameters
#        # this are directly referencable in the script
#        # e.g if OverlapRuns:
#        #    or
#        #    move_to_hole(holeid)
#        #=======================================================================
#
#        d.update(self._context)
#        return d

#    def gosub(self, *args, **kw):
#        kw['analysis_type'] = self.analysis_type
#        kw['_context'] = self._context
#        super(ExtractionPyScript, self).gosub(*args, **kw)

#    @verbose_skip
#    def is_open(self, name=None, description=''):
#        self.info('is {} ({}) open?'.format(name, description))
#        result = self._get_valve_state(name, description)
#        if result:
#            return result[0] == True
#
#    @verbose_skip
#    def is_closed(self, name=None, description=''):
#        self.info('is {} ({}) closed?'.format(name, description))
#        result = self._get_valve_state(name, description)
#        if result:
#            return result[0] == False
#
#    def _get_valve_state(self, name, description):
#        return self._manager_action([('open_valve', (name,), dict(
#                                                      mode='script',
#                                                      description=description
#                                                      ))], protocol=ELPROTOCOL)
