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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.helpers.strtools import to_bool
from pychron.lasers.laser_managers.ilaser_manager import ILaserManager
from pychron.tx.errors import LogicBoardCommErrorCode, InvalidMotorErrorCode, InvalidSampleHolderErrorCode
from pychron.tx.errors import EnableErrorCode
from pychron.tx.errors import InvalidArgumentsErrorCode
from pychron.tx.protocols.service import ServiceProtocol


class LaserProtocol(ServiceProtocol):
    def __init__(self, application, name, addr):
        ServiceProtocol.__init__(self)
        # self._application = application
        man = application.get_service(ILaserManager, 'name=="{}"'.format(name))
        self._manager = man
        self._addr = addr

        services = (('GetError','_get_error'),
                    ('MachineVisionDegas', '_machine_vision_degas'),
                    ('StartVideoRecording', '_start_video_recording'),
                    ('StopVideoRecording', '_stop_video_recording'),
                    ('ReadLaserPower', '_read_laser_power'),
                    ('GetLaserStatus', '_get_laser_status'),
                    ('Snapshot', '_snapshot'),
                    ('PrepareLaser', '_prepare_laser'),
                    ('LaserReady', '_laser_ready'),
                    ('Enable', '_enable'),
                    ('Disable', '_disable'),
                    ('SetXY', '_set_x_y'),
                    ('SetX', '_set_x'),
                    ('SetY', '_set_y'),
                    ('SetZ', '_set_z'),
                    ('GetPosition', '_get_position'),
                    ('GetAutoCorrecting', '_get_auto_correcting'),
                    ('GetDriveMoving', '_get_drive_moving'),
                    ('GetXMoving', '_get_x_moving'),
                    ('GetYMoving', '_get_y_moving'),
                    ('GetZMoving', '_get_z_moving'),
                    ('StopDrive', '_stop_drive'),
                    ('SetDriveHome', '_set_drive_home'),
                    ('SetHomeX', '_set_home_x'),
                    ('SetHomeY', '_set_home_y'),
                    ('SetHomeZ', '_set_home_z'),
                    ('GoToHole', '_go_to_hole'),
                    ('DoPattern', '_do_pattern'),
                    ('IsPatterning', '_is_patterning'),
                    ('AbortPattern', '_abort_pattern'),
                    ('DoJog', '_do_pattern'),
                    ('IsJogging', '_is_patterning'),
                    ('AbortJog', '_abort_pattern'),
                    ('GetJogProcedures', '_get_pattern_names'),
                    ('GetPatternNames', '_get_pattern_names'),
                    ('SetBeamDiameter', '_set_beam_diameter'),
                    ('GetBeamDiameter', '_get_beam_diameter'),
                    ('SetZoom', '_set_zoom'),
                    ('GetZoom', '_get_zoom'),
                    ('SetMotorLock', '_set_motor_lock'),
                    ('SetMotor', '_set_motor'),
                    ('GetMotorMoving', '_get_motor_moving'),
                    ('SetSampleHolder', '_set_sample_holder'),
                    ('GetSampleHolder', '_get_sample_holder'),
                    ('SetLaserPower', '_set_laser_power'),
                    ('SetLaserOutput', '_set_laser_output'),
                    ('GetAchievedOutput', '_get_achieved_output'),
                    ('GetResponseBlob', '_get_response_blob'),
                    ('GetOutputBlob', '_get_output_blob'),
                    ('GoToNamedPosition', '_go_to_named_position'),
                    ('GoToPoint', '_go_to_point'),
                    ('TracePath', '_trace_path'),
                    ('IsTracing', '_is_tracing'),
                    ('StopTrace', '_stop_trace'),
                    ('Prepare', '_prepare'),
                    ('IsReady', '_is_ready'),
                    ('SetLight', '_set_light'))
        self._register_services(services)

    def _get_response(self, service, data):
        cdata = self._prepare_data(data)
        service.callback(self._manager, cdata)

    # ===============================================================================
    # Machine Vision
    # ===============================================================================
    def _machine_vision_degas(self, manager, data):
        if isinstance(data, dict):
            lumens, duration = data['lumens'], data['duration']
        else:
            lumens, duration = data.split(',')

        lumens, duration = float(lumens), float(duration)
        manager.do_machine_vision_degas(lumens, duration, new_thread=True)

    def _get_auto_correcting(self, manager, data):
        return manager.stage_manager.is_auto_correcting()

    # ===============================================================================
    # Video
    # ===============================================================================
    def _start_video_recording(self, manager, data):
        manager.start_video_recording(data)

    def _stop_video_recording(self, manager, data):
        manager.stop_video_recording()

    def _snapshot(self, manager, data):
        """
            name: base name for file. saved in default directory

            returns: abs path to saved file in the media server
        """
        if isinstance(data, dict):
            name, pic_format = data['name'], data['pic_format']
        else:
            name, pic_format = data.split(',')

        sm = manager.stage_manager
        if hasattr(sm, 'video'):
            if pic_format not in ('.jpg', '.png'):
                pic_format = '.jpg'

            lpath, upath, imageblob = sm.snapshot(name=name,
                                                  return_blob=True,
                                                  inform=False,
                                                  pic_format=pic_format)

            s = '{:02X}{}{:02x}{}{}'.format(len(lpath),
                                            lpath, len(upath), upath, imageblob)
            return s

    # ===============================================================================
    # Laser
    # ===============================================================================
    def _get_error(self, manager, data):
        return manager.get_error()

    def _read_laser_power(self, manager, data):
        """
            return watts
        """
        return manager.get_laser_watts()

    def _get_laser_status(self, manager, data):
        return

    def _prepare_laser(self, manager, data):
        manager.prepare_laser()
        return True

    def _laser_ready(self, manager, data):
        return manager.is_laser_ready()

    def _enable(self, manager, data):
        err = manager.enable_laser()
        if err is None:
            err = LogicBoardCommErrorCode()
        elif isinstance(err, str):
            err = EnableErrorCode(err)
        return err

    def _disable(self, manager, data):
        err = manager.disable_laser()
        if err is None:
            err = LogicBoardCommErrorCode()
        elif isinstance(err, str):
            err = EnableErrorCode(err)

    def _set_laser_power(self, manager, data):
        try:
            p = float(data)
        except:
            return InvalidArgumentsErrorCode('SetLaserPower', data)

        manager.set_laser_power(p)
        return True

    def _set_laser_output(self, manager, data):
        if isinstance(data, dict):
            value, units = data['value'], data['units']
        else:
            value, units = data.split(',')

        try:
            p = float(value)
        except:
            return InvalidArgumentsErrorCode('SetLaserOutput', value)

        manager.set_laser_output(p, units)
        return True

    def _get_achieved_output(self, manager, data):
        return manager.get_achieved_output()

    def _get_response_blob(self, manager, data):
        return manager.get_response_blob()

    def _get_output_blob(self, manager, data):
        return manager.get_output_blob()

    # ===============================================================================
    # Motors
    # ===============================================================================
    def _set_beam_diameter(self, manager, data):
        try:
            bd = float(data)
        except ValueError:
            return InvalidArgumentsErrorCode('SetBeamDiameter', data)
        return manager.set_beam_diameter(bd, block=False)

    def _get_beam_diameter(self, manager, data):
        motor = manager.get_motor('beam')
        pos = 'No Beam Motor'
        if motor:
            pos = motor.data_position
        return pos

    def _set_zoom(self, manager, data):
        try:
            zoom = float(data)
        except (ValueError, TypeError):
            return InvalidArgumentsErrorCode('SetZoom', data)

        manager.zoom = zoom
        return True

    def _get_zoom(self, manager, data):
        motor = manager.get_motor('zoom')
        pos = 'No Zoom Motor'
        if motor:
            pos = motor.data_position
        return pos

    def _set_motor_lock(self, manager, name, data):
        return manager.set_motor_lock(name, data)

    def _set_motor(self, manager, name, data):
        try:
            data = float(data)
        except ValueError:
            return InvalidArgumentsErrorCode('SetMotor', data)

        return manager.set_motor(name, data, block=False)

    def _get_motor_moving(self, manager, name):
        motor = manager.get_motor(name)
        if motor is None:
            r = InvalidMotorErrorCode(name)
        else:
            r = motor.is_moving()
        return r

    # ===============================================================================
    # Positioning
    # ===============================================================================
    def _set_x_y(self, manager, data):
        if isinstance(data, dict):
            x,y=data['x'],data['y']
        else:
            x,y=data.split(',')
        # try:
        #     x, y = data.split(',')
        # except (ValueError, AttributeError):
        #     return InvalidArgumentsErrorCode('SetXY', '{}'.format(data))

        try:
            x = float(x)
        except ValueError:
            return InvalidArgumentsErrorCode('SetXY', 'x={}'.format(x))

        try:
            y = float(y)
        except ValueError:
            return InvalidArgumentsErrorCode('SetXY', 'y{}'.format(y))

        # need to remember x,y so we can fool mass spec that we are at position
        manager.stage_manager.temp_position = x, y

        err = manager.stage_manager.set_xy(x, y)

    def _set_x(self, manager, data):
        return self._set_axis(manager, 'x', data)

    def _set_y(self, manager, data):
        return self._set_axis(manager, 'y', data)

    def _set_z(self, manager, data):
        return self._set_axis(manager, 'z', data)

    def _get_position(self, manager, data):
        smanager = manager.stage_manager

        z = smanager.get_z()
        if smanager.temp_position is not None and not smanager.moving():
            x, y = smanager.temp_position
        else:
            x, y = smanager.get_calibrated_xy()

        pos = x, y, z
        return ','.join(['{:0.5f}'.format(i) for i in pos])

    def _get_drive_moving(self, manager, data):
        return manager.stage_manager.moving()

    def _get_x_moving(self, manager, data):
        return manager.stage_manager.moving(axis='x')

    def _get_y_moving(self, manager, data):
        return manager.stage_manager.moving(axis='y')

    def _get_z_moving(self, manager, data):
        return manager.stage_manager.moving(axis='z')

    def _stop_drive(self, manager, data):
        manager.stage_manager.stop()
        return True

    def _set_drive_home(self, manager, data):
        manager.stage_manager.define_home()
        return True

    def _set_home_x(self, manager, data):
        return self._set_home_(manager, axis='x')

    def _set_home_y(self, manager, data):
        return self._set_home_(manager, axis='y')

    def _set_home_z(self, manager, data):
        return self._set_home_(manager, axis='z')

    def _set_sample_holder(self, manager, name):
        if name is None:
            r = InvalidArgumentsErrorCode('SetSampleHolder', name)
        else:
            err = manager.stage_manager._set_stage_map(name)
            if not err:
                r = InvalidSampleHolderErrorCode(name)

        return r

    def _get_sample_holder(self, manager, data):
        return manager.stage_manager.stage_map

    def _go_to_hole(self, manager, hole, autocenter):
        try:
            hole = int(hole)
            autocenter = to_bool(autocenter)
            err = manager.stage_manager.move_to_hole(str(hole),
                                                     correct_position=autocenter)
        except (ValueError, TypeError):
            err = InvalidArgumentsErrorCode('GoToHole', (hole, autocenter))

    def _go_to_named_position(self, manager, data):
        return manager.goto_named_position(data)

    def _go_to_point(self, manager, data):
        return manager.goto_point(data)

    def _trace_path(self, manager, value, pathname, kind):
        return manager.trace_path(value, pathname, kind)

    def _is_tracing(self, manager, data):
        return manager.isTracing()

    def _stop_trace(self, manager, data):
        return manager.stop_trace()

    # ===============================================================================
    # Patterning
    # ===============================================================================
    def _get_pattern_names(self, manager, data):
        ret = ''
        jogs = manager.get_pattern_names()
        if jogs:
            ret = ','.join(jogs)

        return ret

    def _do_pattern(self, manager, name):
        return manager.execute_pattern(name)

    def _is_patterning(self, manager, data):
        return manager.isPatterning()

    def _abort_pattern(self, manager, data):
        return manager.stop_pattern()

    # ===============================================================================
    # Misc
    # ===============================================================================
    def _prepare(self, manager, data):
        return manager.prepare()

    def _is_ready(self, manager, data):
        return manager.is_ready()

    def _set_light(self, manager, data):
        manager.set_light(data)
        return True

    # helpers
    def _set_axis(self, manager, axis, value):
        try:
            d = float(value)
        except (ValueError, TypeError), err:
            return InvalidArgumentsErrorCode('Set{}'.format(axis.upper()), err)

        err = manager.stage_manager.single_axis_move(axis, d)
        return self.error_response(err)

    def _set_home_(self, manager, **kw):
        """
        """
        err = manager.stage_manager.define_home(**kw)
        return self.error_response(err)

# ============= EOF =============================================
