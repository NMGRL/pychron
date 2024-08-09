# ===============================================================================
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
# ===============================================================================

# ============= standard library imports ========================
from __future__ import absolute_import
from __future__ import print_function

import os
import time
from threading import Thread

import six
import six.moves.cPickle as pickle

# ============= enthought library imports =======================
from traits.api import (
    Str,
    String,
    on_trait_change,
    Float,
    Property,
    Instance,
    Event,
    Enum,
    Int,
    Either,
    Range,
    cached_property,
)

from pychron import json

# ============= local library imports  ==========================
from pychron.core.helpers.strtools import to_bool, csv_to_floats
from pychron.envisage.view_util import open_view
from pychron.globals import globalv
from pychron.hardware import get_float, get_blob
from pychron.lasers.laser_managers.ethernet_laser_manager import EthernetLaserManager
from pychron.paths import paths


class PychronLaserManager(EthernetLaserManager):
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

    # communicator = None
    # port = CInt
    # host = Str
    stage_manager_id = "fusions.pychron"
    _cancel_blocking = False

    mode = "client"
    optics_client = Instance("pychron.lasers.laser_managers.client.LaserOpticsClient")
    controls_client = Instance(
        "pychron.lasers.laser_managers.client.LaserControlsClient"
    )

    # def shutdown(self):
    #     if self.communicator:
    #         self.communicator.close()

    def bind_preferences(self, pref_id):
        from apptools.preferences.preference_binding import bind_preference

        bind_preference(self, "use_video", "{}.use_video".format(pref_id))
        self.stage_manager.bind_preferences(pref_id)

        # def open(self):
        #     host = self.host
        #     port = self.port
        #
        #     self.communicator = ec = EthernetCommunicator(host=host,
        #                                                   port=port)
        #     r = ec.open()
        #     if r:
        #         self.connected = True
        #         self.opened()
        #
        #     return r

        # self.trait_set(**dict(zip(('_x', '_y', '_z'),
        #                           self.get_position())))

    def get_tray(self):
        return self._ask("GetSampleHolder")

    def get_error(self):
        error = self._ask("GetError")
        if error is None:
            error = "Get Error Failed"
        return error

    # ===============================================================================
    # patterning
    # ===============================================================================
    def execute_pattern(self, name=None, block=False, duration=None):
        """
        name is either a name of a file
        of a pickled pattern obj
        """
        if name:
            self._patterning = True
            self._execute_pattern(name, block, duration)
            if block:
                self._patterning = False

    def stop_pattern(self):
        self._ask("AbortPattern")
        self._patterning = False

    def get_pattern_names(self):
        # get contents of local pattern_dir
        #         ps = super(PychronLaserManager, self).get_pattern_names()

        ps = []
        # get contents of remote pattern_dir
        pn = self._ask("GetJogProcedures")
        if pn:
            ps.extend(pn.split(","))

        return ps

    # ===============================================================================
    # pyscript commands
    # ===============================================================================
    def wake(self):
        self._ask("WakeScreen")

    def set_light(self, value):
        self._ask("SetLight {}".format(value))

    def acquire_grain_polygon(self):
        return self._ask("AcquireGrainPolygonBlob")

    def start_measure_grain_polygon(self):
        return self._ask("StartMeasureGrainPolygon")

    def stop_measure_grain_polygon(self):
        return self._ask("StopMeasureGrainPolygon")

    def get_grain_polygon_blob(self):
        blobs = []
        if globalv.laser_version > 0:
            while 1:
                blob = self._ask("GetGrainPolygonBlob")
                if blob:
                    if blob == "No Response":
                        break
                    blobs.append(blob)
                else:
                    break

        return blobs

    @get_blob()
    def get_response_blob(self):
        return self._ask("GetResponseBlob", verbose=True)

    @get_blob()
    def get_output_blob(self):
        """
        needs to return bytes. GetOutputBlob sends a b64encoded string

        :return:
        """
        return self._ask("GetOutputBlob")

    @get_float(default=0)
    def get_achieved_output(self):
        return self._ask("GetAchievedOutput")

    @get_float(default=0)
    def get_pyrometer_temperature(self):
        return self._ask("GetPyrometerTemperature")

    # def do_machine_vision_degas(self, lumens, duration):
    #     if lumens and duration:
    #         self.info('Doing machine vision degas. lumens={}'.format(lumens))
    #         self._ask('MachineVisionDegas {},{}'.format(lumens, duration))
    #     else:
    #         self.debug('lumens and duration not set {}, {}'.format(lumens, duration))

    def start_video_recording(self, name):
        self.info("Start Video Recording")
        cmd = {"command": "StartVideoRecording", "name": name}

        self._ask(json.dumps(cmd))

    def stop_video_recording(self):
        self.info("Stop Video Recording")
        return self._ask("StopVideoRecording")

    def take_snapshot(self, name, pic_format, view_snapshot=False):
        self.info("Take snapshot")
        resp = self._ask("Snapshot {},{}".format(name, pic_format))
        if resp:
            args = self._convert_snapshot_response(resp)
            if view_snapshot:
                self._view_snapshot(*args)

            return args

    def prepare(self):
        self.info("Prepare laser")
        self._ask("Prepare")

        cnt = 0
        tries = 0
        maxtries = 200  # timeout after 50 s
        if globalv.experiment_debug:
            maxtries = 1

        nsuccess = 1
        self._cancel_blocking = False
        ask = self._ask
        period = 1
        cmd = "IsReady"
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

    def end_extract(self, *args, **kw):
        self.info("ending extraction. set laser power to 0")
        self.set_laser_power(0)

        if self._patterning:
            self.stop_pattern()

    def extract(self, value, units="", process=None, **kw):
        self.info("set laser output")

        cmd = {"command": "SetLaserOutput", "value": value, "units": units}
        return self._ask(json.dumps(cmd)) == "OK"

        # return self._ask('SetLaserOutput {},{},{}'.format(value, units)) == 'OK'

    def enable_laser(self, *args, **kw):
        self.info("enabling laser")
        return self._ask("Enable") == "OK"

    def disable_laser(self, *args, **kw):
        self.info("disabling laser")
        return self._ask("Disable") == "OK"

    def set_laser_power(self, v, *args, **kw):
        self.info("set laser power {}".format(v))
        return self._ask("SetLaserPower {}".format(v)) == "OK"

    def set_motor_lock(self, name, value):
        v = "YES" if value else "NO"
        self.info("set motor {} lock to {}".format(name, v))
        self._ask("SetMotorLock {},{}".format(name, int(value)))
        return True

    def set_motor(self, name, value):
        self.info("set motor {} to {}".format(name, value))
        self._ask("SetMotor {},{}".format(name, value))
        time.sleep(0.5)
        r = self._block(cmd="GetMotorMoving {}".format(name))
        return r

    def get_position(self):
        xyz = self._ask("GetPosition")
        if xyz:
            try:
                x, y, z = csv_to_floats(xyz)
                return x, y, z
            except Exception as e:
                print("pychron laser manager get_position", e)
                return 0, 0, 0

        if self.communicator.simulation:
            return 0, 0, 0

    # handlers
    # @on_trait_change('pattern_executor:pattern:canceled')
    # def pattern_canceled(self):
    #     """
    #         this patterning window was closed so cancel the blocking loop
    #     """
    #     self._cancel_blocking = True
    def _pattern_executor_init_hook(self, pm):
        def handle():
            self._cancel_blocking = True

        pm.on_trait_change(handle, "pattern:canceled")

    def _snapshot_button_fired(self):
        self.take_snapshot("test", view_snapshot=True)

    def _execute_pattern(self, pat, block, duration):
        self.info("executing pattern {}".format(pat))

        if not pat.endswith(".lp"):
            pat = "{}.lp".format(pat)

        path = os.path.join(paths.pattern_dir, pat)
        if os.path.isfile(path):
            self.debug("Using local pattern {}".format(pat))
            pat = pickle.dumps(path)
            self.debug("Sending Pattern:{}".format(pat))

        self.debug("-------- laser version {}".format(globalv.laser_version))
        if globalv.laser_version > 0:
            cmd = {"command": "DoPattern", "name": pat, "duration": duration}
            cmd = json.dumps(cmd)
        else:
            cmd = "DoPattern {}".format(pat)

        self._ask(cmd, verbose=True)

        if block:
            if isinstance(block, bool):
                timeout = 200
            else:
                timeout = block

            time.sleep(0.5)
            if not self._block("IsPatterning", period=1, timeout=timeout):
                self._ask("AbortPattern")

    # ===============================================================================
    # pyscript private
    # ===============================================================================
    def _view_snapshot(self, local_path, remote_path, image):
        from pychron.lasers.laser_managers.snapshot_view import SnapshotView

        open_required = False
        try:
            sv = self.application.snapshot_view
        except AttributeError:
            sv = None
            open_required = True

        if sv is None:
            sv = SnapshotView()
            self.application.snapshot_view = sv

        sv.set_image(local_path, remote_path, image)
        if open_required:
            info = open_view(sv)
            self.application.snapshot_view_info = info
        else:
            if self.application.snapshot_view_info.control:
                self.application.snapshot_view_info.control.raise_()
            else:
                info = open_view(sv)
                self.application.snapshot_view_info = info

    def _convert_snapshot_response(self, ps):
        """
        ps = XXlpathYYrpathimageblob
        where XX,YY is the len of the following path
        convert ps to a tuple
        """
        l = int(ps[:2], 16)
        e1 = 2 + l
        s1 = ps[2:e1]

        e2 = e1 + 2
        e3 = e2 + int(ps[e1:e2], 16)
        s2 = ps[e2:e3]

        s3 = ps[e3:]
        self.debug("image len {}".format(len(s3)))
        return s1, s2, s3

    def _move_to_position(self, pos, autocenter, block):
        cmd = "GoToHole {},{}".format(pos, autocenter)
        if isinstance(pos, tuple):
            cmd = "SetXY {}".format(pos[:2])
            #            if len(pos) == 3:
        #                cmd = 'SetZ {}'.format(pos[2])

        self.info("sending {}".format(cmd))
        self._ask(cmd)
        time.sleep(0.5)
        r = self._block(nsuccess=3, period=0.5)
        time.sleep(0.5)
        if autocenter and block:
            r = self._block(cmd="GetAutoCorrecting", period=0.5)
            self._ask("CancelAutoCorrecting")

        self.update_position()
        return r

    # def _ask(self, cmd, **kw):
    #     # self.communicator.get_handler()
    #     return self.communicator.ask(cmd, **kw)

    def _set_x(self, v):
        if self._move_enabled:
            self._ask("SetX {}".format(v))
            self.update_position()

    def _set_y(self, v):
        if self._move_enabled:
            self._ask("SetY {}".format(v))
            self.update_position()

    def _set_z(self, v):
        if self._move_enabled:
            self._ask("SetZ {}".format(v))
            self.update_position()

    # defaults
    def _stage_manager_default(self):
        name = self.name.lower()
        if "fusions" in name:
            nn = name[7:]
            name = "fusions_{}".format(nn)

        args = dict(
            name="stage",
            configuration_name="stage",
            # configuration_dir_name = self.configuration_dir_name,
            configuration_dir_name=name,
            parent=self,
        )
        return self._stage_manager_factory(args)

    def _controls_client_default(self):
        from pychron.lasers.laser_managers.client import LaserControlsClient

        return LaserControlsClient(parent=self)

    def _optics_client_default(self):
        from pychron.lasers.laser_managers.client import LaserOpticsClient

        return LaserOpticsClient(parent=self)


class PychronUVLaserManager(PychronLaserManager):
    optics_client = Instance("pychron.lasers.laser_managers.client.UVLaserOpticsClient")
    controls_client = Instance(
        "pychron.lasers.laser_managers.client.UVLaserOpticsClient"
    )
    fire = Event
    stop = Event
    fire_mode = Enum("Burst", "Continuous")
    nburst = Property(depends_on="_nburst")
    _nburst = Int
    mask = Property(String(enter_set=True, auto_set=False), depends_on="_mask")
    _mask = Either(Str, Float)

    masks = Property
    attenuator = String(enter_set=True, auto_set=False)
    # attenuators = Property
    zoom = Range(0.0, 100.0)

    def set_reprate(self, v):
        self._ask("SetReprate {}".format(v))

    def extract(self, power, **kw):
        self._set_nburst(power)

        time.sleep(0.25)
        self._ask("Fire burst")
        time.sleep(0.25)

        self._block("IsFiring", period=0.5)

    def end_extract(self):
        self._ask("Fire stop")

    def trace_path(self, value, name, kind):
        if isinstance(name, list):
            name = name[0]

        # traces need to be prefixed with 'l'
        name = str(name)
        name = name.lower()
        #        if not name.startswith('l'):
        #            name = 'l{}'.format(name)

        cmd = "TracePath {},{},{}".format(value, name, kind)
        self.info("sending {}".format(cmd))
        self._ask(cmd)
        return self._block(cmd="IsTracing")

    def drill_point(self, value, name):
        cmd = "DrillPoint"

    # ===============================================================================
    #
    # ===============================================================================
    def _fire_fired(self):
        if self.fire_mode == "Continuous":
            mode = "continuous"
        else:
            mode = "burst"
        self.firing = True

        self._ask("Fire {}".format(mode))

    def _stop_fired(self):
        self.firing = False
        self._ask("Fire stop")

    @on_trait_change("mask, attenuator, zoom")
    def _motor_changed(self, name, new):
        if new is not None:
            t = Thread(target=self.set_motor, args=(name, new))
            t.start()

    # ===============================================================================
    #
    # ===============================================================================
    def _opened_hook(self):
        nb = self._ask("GetNBurst")
        self._nburst = self._get_int(nb)

        mb = self._ask("GetBurstMode")
        if mb is not None:
            self.fire_mode = "Burst" if mb == "1" else "Continuous"

        self._mask = 0

    def _move_to_position(self, pos, autocenter, block):
        cmd = "GoToPoint"

        # if pos.startswith('t'):
        #    if not TRANSECT_REGEX[0].match(pos):
        #        cmd = None

        if isinstance(pos, (str, six.text_type)):
            if not pos:
                return

            if pos[0].lower() in ["t", "l", "d"]:
                cmd = "GoToNamedPosition"

        if cmd:
            cmd = "{},{}".format(cmd, pos)
            self.info("sending {}".format(cmd))
            self._ask(cmd)
            time.sleep(0.5)
            r = self._block()
            self.update_position()
            return r

    # ===============================================================================
    # property get/set
    # ===============================================================================
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
            self._ask("SetNBurst {}".format(v))
            self._nburst = v

    def _get_nburst(self):
        return self._nburst

    def _set_mask(self, m):
        self._mask = m

    def _get_mask(self):
        return self._mask

    def _validate_mask(self, m):
        if m in self.masks:
            return m
        else:
            try:
                return float(m)
            except ValueError:
                pass

    @cached_property
    def _get_masks(self):
        return self._get_motor_values("mask_names")

    def _get_motor_values(self, name):
        p = os.path.join(paths.device_dir, "fusions_uv", "{}.txt".format(name))
        values = []
        if os.path.isfile(p):
            with open(p, "r") as rfile:
                for lin in rfile:
                    lin = lin.strip()
                    if not lin or lin.startswith("#"):
                        continue
                    values.append(lin)

        return values

    def _controls_client_default(self):
        from pychron.lasers.laser_managers.client import UVLaserControlsClient

        return UVLaserControlsClient(model=self)

    def _optics_client_default(self):
        from pychron.lasers.laser_managers.client import UVLaserOpticsClient

        return UVLaserOpticsClient(model=self)


# ============= EOF =============================================
