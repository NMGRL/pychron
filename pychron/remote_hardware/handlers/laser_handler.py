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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from base_remote_hardware_handler import BaseRemoteHardwareHandler
from pychron.remote_hardware.errors import InvalidArgumentsErrorCode
# from dummies import DummyLM
from pychron.remote_hardware.errors.laser_errors import LogicBoardCommErrorCode, \
    EnableErrorCode, DisableErrorCode, InvalidSampleHolderErrorCode, \
    InvalidMotorErrorCode
from pychron.core.helpers.filetools import to_bool
# from pychron.remote_hardware.errors.error import InvalidDirectoryErrorCode
# from pychron.paths import paths
# import os

class LaserHandler(BaseRemoteHardwareHandler):
    """
    ``LaserHandler`` provides a protocol for interfacing with a pychron laser.
    """
    _elm = None
    _mrm = None
    _lm = None

    def error_response(self, err):
        return 'OK' if (err is None or err is True) else err

    def get_manager(self):
        if self._lm is None:
            self._lm = self.get_laser_manager()
        return self._lm

    def get_elm(self):
        if self._elm is None:
            if self.application:
                protocol = 'pychron.extraction_line.extraction_line_manager.ExtractionLineManager'
                self._elm = self.application.get_service(protocol)

        return self._elm

    def get_mrm(self):
        mrm = None
        elm = self.get_elm()
        if elm is None:
            man = self.get_manager()
            try:
                mrm = man.multruns_report_manager
            except AttributeError:
                pass
        else:
            mrm = elm.multruns_report_manager

        if mrm is None:
            self.info('multrun report manager unavailable')
        return mrm
# ===============================================================================
# Commands
# ===============================================================================
    def MachineVisionDegas(self, manager, lumens, duration, *args):
        manager.do_machine_vision_degas(lumens, duration, new_thread=True)

    def StartVideoRecording(self, manager, name, *args):
        manager.start_video_recording(name)

    def StopVideoRecording(self, manager, *args):
        manager.stop_video_recording()

    def ReadLaserPower(self, manager, *args):
        """
            return watts
        """
        result = manager.get_laser_watts()
        return result

    def GetLaserStatus(self, manager, *args):
        result = 'OK'
        return result

    def Snapshot(self, manager, name, *args):
        """
            name: base name for file. saved in default directory

            returns: abs path to saved file in the media server
        """

        sm = manager.stage_manager
        if hasattr(sm, 'video'):
            pic_format = args[0]
            if pic_format not in ('.jpg','.png'):
                pic_format='.jpg'

            lpath, upath, imageblob = sm.snapshot(name=name,
                                                  return_blob=True,
                                                  inform=False,
                                                  pic_format=pic_format)

            s = '{:02X}{}{:02x}{}{}'.format(len(lpath),
                                             lpath, len(upath), upath, imageblob)

            self.debug('snapshot response={}'.format(s[:40]))
            return s

    def PrepareLaser(self, manager, *args):
        result = 'OK'
        manager.prepare_laser()
        return result

    def LaserReady(self, manager, *args):
        result = manager.is_laser_ready()
        return result

    def Enable(self, manager, *args):
        err = manager.enable_laser()
        if err is None:
            err = LogicBoardCommErrorCode()
        elif isinstance(err, str):
            err = EnableErrorCode(err)

#         def record():
#
#
#             '''
#                 getting the rid needs to be fixed
#
#                 the problem is that instances of pychron can be configured
#                 with a laser but no extraction line manager
#
#                 so laser manager needs to be configured with an
#                 rpc-multruns report manager
#
#             '''
#
#             mrm = self.get_mrm()
#             rid = mrm.get_current_rid() if mrm else 'testrid_001'
#             if manager.record_lasing_power:
#                 manager.start_power_recording(rid)
#
#             try:
#                 if manager.record_lasing_video:
#                     manager.stage_manager.start_recording(basename=rid)
#             except AttributeError:
#                 # not a video stage manager
#                 pass
#
#         t = Thread(target=record)
#         t.start()

        return self.error_response(err)

    def Disable(self, manager, *args):
        err = manager.disable_laser()
        if err is None:
            err = LogicBoardCommErrorCode()
        elif isinstance(err, str):
            err = DisableErrorCode(err)

#         if manager.record_lasing_power:
#             manager.stop_power_recording(delay=5)
#
#         if manager.record_lasing_video:
#             try:
#                 manager.stage_manager.stop_recording(delay=5)
#             except AttributeError:
#                 # not a video stage manager
#                 pass

        return self.error_response(err)

    def SetXY(self, manager, data, *args):
        try:
            x, y = data.split(',')
        except (ValueError, AttributeError):
            return InvalidArgumentsErrorCode('SetXY', '{}'.format(data))

        try:
            x = float(x)
        except ValueError:
            return InvalidArgumentsErrorCode('SetXY', '{}  {}'.format(data, x))

        try:
            y = float(y)
        except ValueError:
            return InvalidArgumentsErrorCode('SetXY', '{}  {}'.format(data, y))

        # need to remember x,y so we can fool mass spec that we are at position
        manager.stage_manager.temp_position = x, y

        err = manager.stage_manager.set_xy(x, y)

        return self.error_response(err)

    def SetX(self, manager, data, *args):
        return self._set_axis(manager, 'x', data)

    def SetY(self, manager, data, *args):
        return self._set_axis(manager, 'y', data)

    def SetZ(self, manager, data, *args):
        return self._set_axis(manager, 'z', data)

    def GetPosition(self, manager, *args):
        """
            returns the cached value

            mass spec excessively calls GetPosition.
            When called during moving it appears to wack out the newport stage controller.
            moving will only do a hardware query if the stage is actually in motion or
            use keyword force_query=True
        """
        smanager = manager.stage_manager

        z = smanager.get_z()
        if smanager.temp_position is not None and not smanager.moving():
            x, y = smanager.temp_position
        else:
            x, y = smanager.get_calibrated_xy()

        pos = x, y, z
        return ','.join(['{:0.5f}' .format(i) for i in pos])

    def GetAutoCorrecting(self, manager):
        return manager.stage_manager.is_auto_correcting()

    def GetDriveMoving(self, manager, *args):
        return manager.stage_manager.moving()

    def GetXMoving(self, manager, *args):
        return manager.stage_manager.moving(axis='x')

    def GetYMoving(self, manager, *args):
        return manager.stage_manager.moving(axis='y')

    def GetZMoving(self, manager, *args):
        return manager.stage_manager.moving(axis='z')

    def StopDrive(self, manager, *args):
        manager.stage_manager.stop()
        return 'OK'

    def SetDriveHome(self, manager, *args):
        manager.stage_manager.define_home()
        return 'OK'

    def SetHomeX(self, manager, *args):
        return self._set_home_(manager, axis='x')

    def SetHomeY(self, manager, *args):
        return self._set_home_(manager, axis='y')

    def SetHomeZ(self, manager, *args):
        return self._set_home_(manager, axis='z')

    def GoToHole(self, manager, hole, autocenter, *args):
        try:
            hole = int(hole)
            autocenter = to_bool(autocenter)

            err = manager.stage_manager.move_to_hole(str(hole),
                                                     correct_position=autocenter)
        except (ValueError, TypeError):
            err = InvalidArgumentsErrorCode('GoToHole', (hole, autocenter))

        return self.error_response(err)

    def GetPatternNames(self, manager, *args):
        ret=''
        jogs = manager.get_pattern_names()
        if jogs:
            ret=','.join(jogs)

        return ret

    def DoPattern(self, manager, name, *args, **kw):
        if name is None:
            err = InvalidArgumentsErrorCode('DoJog', name)
        else:
            err = manager.execute_pattern(name)
        return self.error_response(err)

    def IsPatterning(self, manager, *args, **kw):
        err = manager.isPatterning()
        return self.error_response(str(err))

    def AbortPattern(self, manager, *args, **kw):
        err = manager.stop_pattern()
        return self.error_response(err)

    DoJog = DoPattern
    IsJogging = IsPatterning
    AbortJog = AbortPattern
    GetJogProcedures = GetPatternNames

    def SetBeamDiameter(self, manager, data, *args):
        try:
            bd = float(data)
        except ValueError:
            return InvalidArgumentsErrorCode('SetBeamDiameter', data, logger=self)

        if manager.set_beam_diameter(bd, block=False):
            return 'OK'
        else:
            return 'OK - beam disabled'

    def GetBeamDiameter(self, manager, *args):
        motor = manager.get_motor('beam')
        pos = 'No Beam Motor'
        if motor:
            pos = motor.data_position
        return pos

    def SetZoom(self, manager, data, *args):
        try:
            zoom = float(data)
        except (ValueError, TypeError):
            return InvalidArgumentsErrorCode('SetZoom', data, logger=self)

        manager.zoom = zoom
        return 'OK'

    def GetZoom(self, manager, *args):
        motor = manager.get_motor('zoom')
        pos = 'No Zoom Motor'
        if motor:
            pos = motor.data_position
        return pos

    def SetMotorLock(self, manager, name, data, *args):
        if manager.set_motor_lock(name, data):
            return 'OK'
        else:
            return 'OK - {} disabled'.format(name)

    def SetMotor(self, manager, name, data, *args):
        try:
            data = float(data)
        except ValueError:
            return InvalidArgumentsErrorCode('SetMotor', data, logger=self)

        if manager.set_motor(name, data, block=False):
            return 'OK'
        else:
            return 'OK - {} disabled'.format(name)

    def GetMotorMoving(self, manager, name, *args):
        motor = manager.get_motor(name)
        if motor is None:
            r = InvalidMotorErrorCode(name, logger=self)
        else:
            r = motor.is_moving()
        return r

    def SetSampleHolder(self, manager, name, *args):
        if name is None:
            r = InvalidArgumentsErrorCode('SetSampleHolder', name)
        else:
            err = manager.stage_manager._set_stage_map(name)
            if err is True:
                r = 'OK'
            else:
                r = InvalidSampleHolderErrorCode(name)

        return r

    def GetSampleHolder(self, manager, *args):
        return manager.stage_manager.stage_map

    def SetLaserPower(self, manager, data, *args):
        result = 'OK'
        try:
            p = float(data)
        except:
            return InvalidArgumentsErrorCode('SetLaserPower', data, logger=self)

        manager.set_laser_power(p)
        return result

    def SetLaserOutput(self, manager, value, units, *args):
        result = 'OK'
        try:
            p = float(value)
        except:
            return InvalidArgumentsErrorCode('SetLaserOutput', value, logger=self)

        manager.set_laser_output(p, units)
        return result

    def GetAchievedOutput(self, manager, *args):
        result=manager.get_achieved_output()
        return str(result)

    def GetResponseBlob(self, manager, *aregs):
        result = manager.get_response_blob()
        return str(result)

    def GetOutputBlob(self, manager, *aregs):
        result = manager.get_output_blob()
        return str(result)

        # ===============================================================================

        # Positioning

    # ===============================================================================
    def GoToNamedPosition(self, manager, pos, *args):
        result = manager.goto_named_position(pos)
        return result

    def GoToPoint(self, manager, pos, *args):
        result = manager.goto_point(pos)
        return result

    def TracePath(self, manager, value, pathname, kind, *args):
        result = manager.trace_path(value, pathname, kind)
        return result

    def IsTracing(self, manager, *args):
        result = manager.isTracing()
        return result

    def StopTrace(self, manager, *args):
        result = manager.stop_trace()
        return result

    def Prepare(self, manager, *args):
        result = manager.prepare()
        return result

    def IsReady(self, manager, *args):
        result = manager.is_ready()
        return result

    def SetLight(self,manager, value, *args):
        manager.set_light(value)
        return 'OK'

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

# ===============================================================================
#
# ===============================================================================
#     def DoJog(self, manager, name, *args):
#         if name is None:
#             err = InvalidArgumentsErrorCode('DoJog', name)
#         else:
#
# #            err = manager.stage_manager.pattern_manager.execute_pattern(name)
#             err = manager.execute_pattern(name)
#         return self.error_response(err)

#     def AbortJog(self, manager, *args):
#         err = manager.stop_pattern()
#         return self.error_response(err)

#     def IsJogging(self, manager, *args):
#         err = manager.isPatterning()
#
#         # returns "True" or "False"
#         return self.error_response(str(err))

#    def ListDirectory(self, manager, name, ext, *args):
#        p = ''
#        if hasattr(paths, name):
#            p = getattr(paths, name)
#        elif hasattr(paths, '{}_dir'.format(name)):
#            p = getattr(paths, '{}_dir'.format(name))
#
#        if os.path.exists(p):
#            if os.path.isdir(p):
#                result = 'fooo'
#                def func(x):
#                    if x.startswith('.'):
#                        return
#                    if ext.startswith('.'):
#                        return x.endswith(ext)
#                    else:
#                        return True
#                ps = filter(func, os.listdir(p))
#                result = ','.join(ps)
#
#            else:
#                result = InvalidDirectoryErrorCode(name, style=2)
#        else:
#            result = InvalidDirectoryErrorCode(name)
#
#        return result

# ============= EOF ====================================
