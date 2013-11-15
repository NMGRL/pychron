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

#============= standard library imports ========================
from threading import Thread
#============= local library imports  ==========================
from pychron.remote_hardware.errors import InvalidArgumentsErrorCode, InvalidValveErrorCode, \
    InvalidIPAddressErrorCode, ValveSoftwareLockErrorCode, ValveActuationErrorCode
from base_remote_hardware_handler import BaseRemoteHardwareHandler
from dummies import DummyELM
# from pychron.envisage.core.action_helper import open_manager
from pychron.remote_hardware.errors.extraction_line_errors import InvalidGaugeErrorCode

EL_PROTOCOL = 'pychron.extraction_line.extraction_line_manager.ExtractionLineManager'
TM_PROTOCOL = 'pychron.social.twitter_manager.TwitterManager'
RHM_PROTOCOL = 'pychron.remote_hardware.remote_hardware_manager.RemoteHardwareManager'


class ExtractionlineHandler(BaseRemoteHardwareHandler):
    extraction_line_manager = None
    manager_name = 'extraction_line_manager'

    def get_manager(self):

        if self.extraction_line_manager is None:
            if self.application is not None:
                elm = self.application.get_service(EL_PROTOCOL)
            else:
                elm = DummyELM()
            self.extraction_line_manager = elm
        else:
            elm = self.extraction_line_manager

        return elm

    #    def get_device(self, name, protocol=None):
    #        if self.application is not None:
    #            if protocol is None:
    #                protocol = 'pychron.hardware.core.i_core_device.ICoreDevice'
    #            dev = self.application.get_service(protocol, 'name=="{}"'.format(name))
    #            if dev is None:
    #                #possible we are trying to get a flag
    #                m = self.get_manager()
    #                dev = m.get_flag(name)
    #
    #        else:
    #            dev = DummyDevice()
    #        return dev

    def Open(self, manager, vname, sender_address, *args):
        # intercept flags
        if vname.endswith('Flag'):
            r = self.Set(manager, vname, 1, sender_address, *args)
            return 'OK' if r else 'Error setting flag'

        result, change = manager.open_valve(vname,
                                            sender_address=sender_address)

        if result == True:
            result = 'OK' if change else 'ok'
        elif result is None:
            result = InvalidArgumentsErrorCode('Open', vname, logger=self)
        elif result == 'software lock enabled':
            result = ValveSoftwareLockErrorCode(vname, logger=self)
        else:
            result = ValveActuationErrorCode(vname, 'open', logger=self)

        return result

    def Close(self, manager, vname, sender_address, *args):
        # intercept flags
        if vname.endswith('Flag'):
            r = self.Set(manager, vname, 0, sender_address, *args)
            return 'OK' if r else 'Error clearing flag'

        result, change = manager.close_valve(vname,
                                             sender_address=sender_address)
        if result == True:
            result = 'OK' if change else 'ok'
        elif result is None:
            result = InvalidArgumentsErrorCode('Close', vname, logger=self)
        elif result == 'software lock enabled':
            result = ValveSoftwareLockErrorCode(vname, logger=self)
        else:
            result = ValveActuationErrorCode(vname, 'close', logger=self)

        return result

    def GetValveState(self, manager, vname, *args):
        result = manager.get_valve_state(vname)
        if result is None:
            result = InvalidValveErrorCode(vname)
        return result

    def GetValveStates(self, manager, *args):
        result = manager.get_valve_states()
        #        if result is None:
        #            result = 'ERROR'
        return result

    def GetValveLockStates(self, manager, *args):
        result = manager.get_valve_lock_states()
        #        if result is None:
        #            result = 'ERROR'
        return result

    def GetValveLockState(self, manager, vname, *args):
        result = manager.get_software_lock(vname)
        return result

    def GetValveOwners(self, manager, *args):
        manager.debug('get valve owners')
        result = manager.get_valve_owners()
        return result

    def GetManualState(self, manager, vname, *args):
        result = manager.get_software_lock(vname)
        if result is None:
            result = InvalidValveErrorCode(vname)
            #            result = 'ERROR: {} name available'.format(vname)
        #            result = False

        return result

    def StartRun(self, manager, *args):
        '''
            data is a str in form:
            RID,Sample,Power/Temp
        '''
        data = ' '.join(args[:-1])
        if manager.multruns_report_manager is not None:
            run = manager.multruns_report_manager.start_run(data)

            if run and run.kind == 'co2':
                lm = self.get_laser_manager(name='co2')
                if lm is not None:
                    self.application.open_view(lm)

        if self.application is not None:
            tm = self.application.get_service(TM_PROTOCOL)
            if tm is not None:
                tm.post('Run {} started'.format(data))

        return 'OK'

    def CompleteRun(self, manager, *args):
        '''
            complete run should report age
        '''

        data = ' '.join(args[:-1])
        mrm = manager.multruns_report_manager
        if mrm is not None:
            run = mrm.complete_run()

            # clean up any open windows
            # close power recording, close autocenter
            if run and run.kind == 'co2':
                lm = self.get_laser_manager(name='co2')
                if lm is not None:
                    lm.dispose_optional_windows()

        if self.application is not None:
            tm = self.application.get_service(TM_PROTOCOL)
            if tm is not None:
                if 'cancel' in data.lower():
                    tm.post('Run {}'.format(data))
                else:
                    tm.post('Run {} completed'.format(data))

        return 'OK'

    def StartMultRuns(self, manager, *args):
        '''
            data should be str of form:
            NSamples,
        '''
        sender_addr = args[-1]
        data = ' '.join(args[:-1])
        if self.application is not None:

            rhm = self.application.get_service(RHM_PROTOCOL)
            if rhm.lock_by_address(sender_addr, lock=True):

                if manager.multruns_report_manager is not None:
                    manager.multruns_report_manager.start_new_report(data)

                tm = self.application.get_service(TM_PROTOCOL)
                if tm is not None:
                    tm.post('Mult runs start {}'.format(data))
            else:
                return InvalidIPAddressErrorCode(sender_addr)
        return 'OK'

    def CompleteMultRuns(self, manager, *args):

        sender_addr = args[-1]
        data = ' '.join(args[:-1])

        if self.application is not None:

            rhm = self.application.get_service(RHM_PROTOCOL)
            if rhm.lock_by_address(sender_addr, lock=False):
                if manager.multruns_report_manager is not None:
                    tar = manager.multruns_report_manager.complete_report
                    t = Thread(target=tar)
                    t.start()

                tm = self.application.get_service(TM_PROTOCOL)
                if tm is not None:
                    tm.post('Mult runs completed {}'.format(data))
            else:
                return InvalidIPAddressErrorCode(sender_addr)

        return 'OK'

    def SystemLock(self, manager, name, onoff, sender_addr, *args):

        cp = manager.remote_hardware_manager.command_processor
        rhm = self.application.get_service(RHM_PROTOCOL)
        if rhm.validate_address(sender_addr):
            cp.system_lock = onoff in ['On', 'on', 'ON']
            if onoff:
                cp.system_lock_address = sender_addr
        else:
            return InvalidIPAddressErrorCode(sender_addr)

        return 'OK'

    def PychronScript(self, manager, name, *args):
        result = manager.execute_pyscript(name)

        # result should be a unique key that mass spec can use to identify this
        # script

        return result

    def ScriptState(self, manager, uuid, *args):
        result = manager.get_script_state(uuid)
        return result

    def GetPressure(self, manager, controller, gauge):
        p = None
        if manager:
            p = manager.get_pressure(controller, gauge)

        if p is None:
            p = InvalidGaugeErrorCode(controller, gauge)

        return str(p)

#===============================================================================
# not current used
#===============================================================================
#     def ClaimGroup(self, manager, grp, sender_addr, *args):
#         rhm = self.application.get_service(RHM_PROTOCOL)
#         if rhm.validate_address(sender_addr):
#             err = manager.claim_section(grp, sender_addr)
#             if err is True:
#                 return InvalidValveGroupErrorCode(grp)
#         else:
#             return InvalidIPAddressErrorCode(sender_addr)
#
#         return 'OK'
#
#     def ReleaseGroup(self, manager, grp, sender_addr, *args):
#         rhm = self.application.get_service(RHM_PROTOCOL)
#         if rhm.validate_address(sender_addr):
#             err = manager.release_section(grp)
#             if err:
#                 return InvalidValveGroupErrorCode(grp)
#         else:
#             return InvalidIPAddressErrorCode(sender_addr)
#
#         return 'OK'
#
#

#============= EOF ====================================
