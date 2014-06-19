#===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import CInt, Str, String, on_trait_change, Button, Float, \
    Property, Bool, Instance

from traitsui.api import View, Item, VGroup, HGroup, RangeEditor, EnumEditor
import apptools.sweet_pickle as pickle
#============= standard library imports ========================
import time
from threading import Thread
#============= local library imports  ==========================
from pychron.globals import globalv
from pychron.hardware.core.communicators.ethernet_communicator import EthernetCommunicator
from pychron.lasers.laser_managers.client import UVLaserOpticsClient, UVLaserControlsClient,\
    LaserOpticsClient, LaserControlsClient
from pychron.lasers.laser_managers.laser_manager import BaseLaserManager
from pychron.core.helpers.filetools import to_bool
import os
from pychron.paths import paths


class PychronLaserManager(BaseLaserManager):
    """
    A PychronLaserManager is used to control an instance of
    pychron remotely.

    Common laser functions such as enable_laser are converted to
    the RemoteHardwareServer equivalent and sent by the communicator

    e.g enable_laser ==> self.communicator.ask('Enable')

    The communicators connection arguments are set in initialization.xml

    use a communicator block
    <plugin enabled="true" fire_mode="client">FusionsDiode
        ...
        <communications>
          <host>129.138.12.153</host>
          <port>1069</port>
          <kind>UDP</kind>
        </communications>
    </plugin>
    """
    communicator = None
    port = CInt
    host = Str

    _cancel_blocking = False

    position = String(enter_set=True, auto_set=False)
    x = Property(depends_on='_x')
    y = Property(depends_on='_y')
    z = Property(depends_on='_z')
    _x = Float
    _y = Float
    _z = Float
    connected = Bool
    test_connection_button = Button('Test Connection')
    use_autocenter = Bool(False)

    mode = 'client'
    optics_client = Instance(LaserOpticsClient)
    controls_client = Instance(LaserControlsClient)

    def _controls_client_default(self):
        return LaserControlsClient(parent=self)

    def _optics_client_default(self):
        return LaserOpticsClient(parent=self)
    
    def _test_connection_button_fired(self):
        self.test_connection()
        if self.connected:
            self.opened(None)

    def shutdown(self):
        if self.communicator:
            self.communicator.close()

    def _test_connection(self):
        self.connected = self.communicator.open()
        self.debug('test connection. connected= {}'.format(self.connected))
        return self.connected

    def bind_preferences(self, pref_id):
        from apptools.preferences.preference_binding import bind_preference

        bind_preference(self, 'use_video', '{}.use_video'.format(pref_id))
        self.stage_manager.bind_preferences(pref_id)

    def open(self):
        host = self.host
        port = self.port

        self.communicator = ec = EthernetCommunicator(host=host,
                                                       port=port)
        r = ec.open()
        if r:
            self.connected = True
        return r

    def opened(self, ui):
        self.update_position()
        self._opened_hook()

    def _opened_hook(self):
        pass

    def update_position(self):
        self.trait_set(**dict(zip(('_x', '_y', '_z'),
                                  self.get_position())))

    #===============================================================================
    # patterning
    #===============================================================================
    def execute_pattern(self, name=None, block=False):
        """
            name is either a name of a file
            of a pickled pattern obj
        """
        if name:
            return self._execute_pattern(name)

    def _execute_pattern(self, pat):
        self.info('executing pattern {}'.format(pat))

        if not pat.endswith('.lp'):
            pat = '{}.lp'.format(pat)

        path = os.path.join(paths.pattern_dir, pat)
        if os.path.isfile(path):
            self.debug('Using local pattern {}'.format(pat))
            pat = pickle.dumps(path)
            self.debug('Sending Pattern:{}'.format(pat))

        cmd = 'DoPattern {}'.format(pat)
        self._ask(cmd, verbose=False)

        time.sleep(0.5)

        if not self._block('IsPatterning', period=1):
            cmd = 'AbortPattern'
            self._ask(cmd)

    def stop_pattern(self):
        self._ask('AbortPattern')

    @on_trait_change('pattern_executor:pattern:canceled')
    def pattern_canceled(self):
        """
            this patterning window was closed so cancel the blocking loop
        """
        self._cancel_blocking = True

    def get_pattern_names(self):
    # get contents of local pattern_dir
    #         ps = super(PychronLaserManager, self).get_pattern_names()

        ps = []
        # get contents of remote pattern_dir
        pn = self._ask('GetJogProcedures')
        if pn:
            ps.extend(pn.split(','))

        return ps

    #===============================================================================
    # pyscript commands
    #===============================================================================
    def get_response_blob(self):
        return self._ask('GetResponseBlob')

    def get_output_blob(self):
        return self._ask('GetOutputBlob')

    def get_achieved_output(self):
        rv=0
        v=self._ask('GetAchievedOutput')
        if v is not None:
            try:
                rv=float(v)
            except ValueError:
                pass
        return rv

    def do_machine_vision_degas(self, lumens, duration):
        if lumens and duration:
            self.info('Doing machine vision degas. lumens={}'.format(lumens))
            self._ask('MachineVisionDegas {} {}'.format(lumens, duration))
        else:
            self.debug('lumens and duration not set {}, {}'.format(lumens, duration))

    def start_video_recording(self, name):
        self.info('Start Video Recording')
        self._ask('StartVideoRecording {}'.format(name))

    def stop_video_recording(self):
        self.info('Stop Video Recording')
        self._ask('StopVideoRecording')

    def take_snapshot(self, name):
        self.info('Take snapshot')
        self._ask('Snapshot {}'.format(name))

    def prepare(self):
        self.info('Prepare laser')
        self._ask('Prepare')

        cnt = 0
        tries = 0
        maxtries = 200  # timeout after 50 s
        if globalv.experiment_debug:
            maxtries = 1

        nsuccess = 1
        self._cancel_blocking = False
        ask = self._ask
        period = 1
        cmd = 'IsReady'
        while tries < maxtries and cnt < nsuccess:
            if self._cancel_blocking:
                break
            time.sleep(period)
            resp = ask(cmd)
            if resp is not None:
                try:
                    if to_bool(resp):
                        cnt += 1
                except:
                    cnt = 0
            else:
                cnt = 0
            tries += 1

        return cnt >= nsuccess

    def extract(self, value, units=''):
        self.info('set laser output')
        return self._ask('SetLaserOutput {} {}'.format(value, units)) == 'OK'

    def enable_laser(self, *args, **kw):
        self.info('enabling laser')
        return self._ask('Enable') == 'OK'

    def disable_laser(self, *args, **kw):
        self.info('disabling laser')
        return self._ask('Disable') == 'OK'

    def set_laser_power(self, v, *args, **kw):
        self.info('set laser power {}'.format(v))
        return self._ask('SetLaserPower {}'.format(v)) == 'OK'

    def set_motor_lock(self, name, value):
        v = 'YES' if value else 'NO'
        self.info('set motor {} lock to {}'.format(name, v))
        self._ask('SetMotorLock {} {}'.format(name, int(value)))
        return True

    def set_motor(self, name, value):
        self.info('set motor {} to {}'.format(name, value))
        self._ask('SetMotor {} {}'.format(name, value))
        time.sleep(0.5)
        r = self._block(cmd='GetMotorMoving {}'.format(name))
        return r

    def get_position(self):
        xyz = self._ask('GetPosition')
        if xyz:
            try:
                x, y, z = map(float, xyz.split(','))
                return x, y, z
            except Exception, e:
                print 'pychron laser manager get_position', e
                return 0, 0, 0

        if self.communicator.simulation:
            return 0, 0, 0
            #===============================================================================
            # pyscript private
            #===============================================================================

    def _move_to_position(self, pos, autocenter):
        cmd = 'GoToHole {} {}'.format(pos, autocenter)
        if isinstance(pos, tuple):
            cmd = 'SetXY {}'.format(pos[:2])
            #            if len(pos) == 3:
        #                cmd = 'SetZ {}'.format(pos[2])

        self.info('sending {}'.format(cmd))
        self._ask(cmd)
        time.sleep(0.5)
        r = self._block()
        if autocenter:
            r = self._block(cmd='GetAutoCorrecting', period=0.5)

        self.update_position()
        return r

    def _block(self, cmd='GetDriveMoving', period=0.25, position_callback=None):

        ask = self._ask

        cnt = 0
        tries = 0
        maxtries = int(50 / float(period))  # timeout after 50 s
        nsuccess = 2
        self._cancel_blocking = False
        while tries < maxtries and cnt < nsuccess:
            if self._cancel_blocking:
                break

            time.sleep(period)
            resp = ask(cmd)

            if self.communicator.simulation:
                resp = 'False'

            if resp is not None:
                try:
                    if not to_bool(resp):
                        cnt += 1
                except (ValueError, TypeError):
                    cnt = 0

                if position_callback:
                    if self.communicator.simulation:
                        x, y, z = cnt / 3., cnt / 3., 0
                        position_callback(x, y, z)
                    else:
                        xyz = self.get_position()
                        if xyz:
                            position_callback(*xyz)
            else:
                cnt = 0
            tries += 1

        state = cnt >= nsuccess
        if state:
            self.info('Block completed')
        else:
            if self._cancel_blocking:
                self.info('Block failed. canceled by user')
            else:
                self.warning('Block failed. timeout after {}s'.format(maxtries * period))

        return state

    def _ask(self, cmd, **kw):
        self.communicator.get_handler()
        return self.communicator.ask(cmd, **kw)

    def _enable_fired(self):
        if self.enabled:
            self.disable_laser()
            self.enabled = False
        else:
            if self.enable_laser():
                self.enabled = True

    def _position_changed(self):
        if self.position is not None:
            t = Thread(target=self._move_to_position,
                       args=(self.position, self.use_autocenter))
            t.start()
            self._position_thread = t
            #     def traits_view(self):
            #         v = View(
            #                  Item('test_connection_button', show_label=False),
            #                  self.get_control_button_group(),
            #                  Item('position'),
            #                  Item('x', editor=RangeEditor(low= -25.0, high=25.0)),
            #                  Item('y', editor=RangeEditor(low= -25.0, high=25.0)),
            #                  Item('z', editor=RangeEditor(low= -25.0, high=25.0)),
            #                  title='Laser Manager',
            #                  handler=self.handler_klass
            #                  )
            #         return v

    def _set_x(self, v):
        self._ask('SetX {}'.format(v))
        self.update_position()

    #        self._x=v

    def _set_y(self, v):
        self._ask('SetY {}'.format(v))
        self.update_position()

    #        self._y=v

    def _set_z(self, v):
        self._ask('SetZ {}'.format(v))
        self.update_position()

    #        self._z=v

    def _get_x(self):
        return self._x

    def _get_y(self):
        return self._y

    def _get_z(self):
        return self._z

    def _stage_manager_default(self):
        '''
        '''

        args = dict(name='stage',
                    configuration_name='stage',
                    configuration_dir_name=self.name,
                    parent=self,
        )
        return self._stage_manager_factory(args)


class PychronUVLaserManager(PychronLaserManager):
    optics_client = Instance(UVLaserOpticsClient)
    controls_client = Instance(UVLaserControlsClient)

    def _controls_client_default(self):
        return UVLaserControlsClient(parent=self)

    def _optics_client_default(self):
        return UVLaserOpticsClient(parent=self)

    def set_reprate(self, v):
        self._ask('SetReprate {}'.format(v))

    def extract(self, power, **kw):
        self._set_nburst(power)

        time.sleep(0.25)
        self._ask('Fire burst')
        time.sleep(0.25)

        self._block('IsFiring', period=0.5)

    def end_extract(self):
        self._ask('Fire stop')

    def trace_path(self, value, name, kind):
        if isinstance(name, list):
            name = name[0]

        # traces need to be prefixed with 'l'
        name = str(name)
        name = name.lower()
        #        if not name.startswith('l'):
        #            name = 'l{}'.format(name)

        cmd = 'TracePath {} {} {}'.format(value, name, kind)
        self.info('sending {}'.format(cmd))
        self._ask(cmd)
        return self._block(cmd='IsTracing')

    def drill_point(self, value, name):
        cmd = 'DrillPoint'

    #===============================================================================
    #
    #===============================================================================
    def _fire_fired(self):
        if self.firing:
            mode = 'stop'
            self.firing = False
        else:
            if self.fire_mode == 'Continuous':
                mode = 'continuous'
            else:
                mode = 'burst'
            self.firing = True

        self._ask('Fire {}'.format(mode))

        #     def _position_changed(self):
        #         if self.position is not None:
        #             t = Thread(target=self._move_to_position, args=(self.position,))
        #             t.start()
        # #            self._move_to_position(self.position)

        #===============================================================================
        #
        #===============================================================================

    def _opened_hook(self):
        nb = self._ask('GetNBurst')
        self._nburst = self._get_int(nb)

        mb = self._ask('GetBurstMode')
        if mb is not None:
            self.fire_mode = 'Burst' if mb == '1' else 'Continuous'

            #    def _set_motor(self, name, value):
            #        self.info('setting motor {} to {}'.format(name,value))
            #        cmd='SetMotor {} {}'.format(name, value)
            #        time.sleep(0.5)
            #        self._ask(cmd)
            #        r = self._block(cmd='GetMotorMoving {}'.format(name))
            #        return r

    def _move_to_position(self, pos, autocenter):

        cmd = 'GoToPoint'

        #if pos.startswith('t'):
        #    if not TRANSECT_REGEX[0].match(pos):
        #        cmd = None

        if isinstance(pos, (str, unicode)):
            if not pos:
                return

            if pos[0].lower() in ['t', 'l', 'd']:
                cmd = 'GoToNamedPosition'

        if cmd:
            cmd = '{} {}'.format(cmd, pos)
            self.info('sending {}'.format(cmd))
            self._ask(cmd)
            time.sleep(0.5)
            r = self._block()
            self.update_position()
            return r

    def traits_view(self):
        v = View(Item('test_connection_button', show_label=False),
                 VGroup(
                     self.get_control_button_group(),
                     HGroup(self._button_factory('fire', 'fire_label', enabled='enabled'),
                            Item('fire_mode', show_label=False),
                            Item('nburst')
                     ),
                     Item('position'),
                     Item('zoom', style='simple'),
                     HGroup(Item('mask', editor=EnumEditor(name='masks')), Item('mask', show_label=False)),
                     HGroup(Item('attenuator', editor=EnumEditor(name='attenuators')),
                            Item('attenuator', show_label=False)),
                     Item('x', editor=RangeEditor(low=-25.0, high=25.0)),
                     Item('y', editor=RangeEditor(low=-25.0, high=25.0)),
                     Item('z', editor=RangeEditor(low=-25.0, high=25.0)),
                     enabled_when='connected'
                 ),
                 title='Laser Manager',
                 handler=self.handler_klass
        )
        return v

    #===============================================================================
    # property get/set
    #===============================================================================


    def _get_int(self, resp):
        r = 0
        if resp is not None:
            try:
                r = int(resp)
            except (ValueError, TypeError):
                pass
        return r

    def _validate_nburst(self, v):
        try:
            return int(v)
        except (ValueError, TypeError):
            pass

    def _set_nburst(self, v):
        if v is not None:
            v = int(v)
            self._ask('SetNBurst {}'.format(v))
            self._nburst = v

    def _get_nburst(self):
        return self._nburst

    def _get_fire_label(self):
        return 'Stop' if self.firing else 'Fire'

        #        else:

#
#            return super(PychronUVLaserManager, self)._move_to_position(pos)

#============= EOF =============================================
