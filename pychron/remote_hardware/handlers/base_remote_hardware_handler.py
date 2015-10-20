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
from traits.api import Any, Instance
# ============= standard library imports ========================
import shlex
# ============= local library imports  ==========================
# from dummies import DummyDevice, DummyLM
from error_handler import ErrorHandler
from pychron.loggable import Loggable
from pychron.remote_hardware.errors import DeviceConnectionErrorCode
from pychron.lasers.laser_managers.ilaser_manager import ILaserManager

cnt = 0
gErrorSet = False


class BaseRemoteHardwareHandler(Loggable):
    application = Any
    error_handler = Instance(ErrorHandler, ())
    manager_name = 'Manager'

    def parse(self, data):
        args = data.split(' ')
        return args[0], ' '.join(args[1:])

    def handle(self, data, sender_addr, lock):
        with lock:
            eh = self.error_handler
            manager = self.get_manager()
            err = eh.check_manager(manager, self.manager_name)
            if err is None:
                # str list split by shlex
                # first arg is the command
                args = self.split_data(data)
                # try:
                err, func = eh.check_command(self, args)
                # except InvalidCommandErrorCode, e:
                #    err = e

                if err is None:
                    err, response = eh.check_response(func, manager, args[1:] +
                                                      [sender_addr])
                    # print 'err: {} response: {}'.format(err, response)
                    if err is None:
                        return response

        return str(err)

    def get_manager(self):
        return

    def split_data(self, data):
        return [a.strip() for a in shlex.split(data)]

    def get_func(self, fstr):
        try:
            return getattr(self, fstr)

        except AttributeError:
            pass

    def get_device(self, name, protocol=None, owner=None):
        dev = None
        if self.application is not None:
            if protocol is None:
                protocol = 'pychron.hardware.core.i_core_device.ICoreDevice'
            dev = self.application.get_service(protocol, 'name=="{}"'.format(name))
            if dev is None:
                # possible we are trying to get a flag
                m = self.get_manager()
                if m:
                    dev = m.get_flag(name)
                    if dev is None:
                        dev = m.get_mass_spec_param(name)
                    else:
                        if owner:
                            dev.set_owner(owner)

        #         else:
        #             dev = DummyDevice()
        # else:
        #     dev = DummyDevice()
        return dev

    def get_laser_manager(self, name=None):
        lm = None
        if name is None:
            name = self.manager_name

        if self.application is not None:
            lm = self.application.get_service(ILaserManager, 'name=="{}"'.format(name))
        # else:
        #     lm = DummyLM()

        return lm

    def GetError(self, manager, *args):
        return manager.get_error()

    def Set(self, manager, dname, value, *args):
        d = self.get_device(dname)
        if d is not None:
            self.info('Set {} to {}'.format(d.name,
                                            value))
            result = d.set(value)
        else:
            result = DeviceConnectionErrorCode(dname, logger=self)

        return result

    def Read(self, manager, dname, sender, *args):
        d = self.get_device(dname, owner=sender)
        if d is not None:
            result = d.get(current=True)
            self.debug('Read owner={}'.format(sender))
            self.info('Get {} = {}'.format(d.name, result))
        else:
            result = DeviceConnectionErrorCode(dname, logger=self)
        return result

    def PychronReady(self, *args, **kw):
        return 'OK'

    def WakeScreen(self):
        from pychron.core.ui.gui import wake_screen
        wake_screen()

#    def RemoteLaunch(self, *args, **kw):
#        return False

# ===============================================================================
# ##testing interface
# ===============================================================================

    def ReadTest(self, *args, **kw):
        global cnt
        global gErrorSet
        cnt += 1
        r = cnt
        if cnt > 11:
            cnt = 0

        if gErrorSet:
            cnt = 0
            gErrorSet = False
            r = 'Error 501 : Global error set'
        return r

    def SendTest(self, *args, **kw):
        return 'OK'

    def Watch(self):
        global gErrorSet
        gErrorSet = True
        return 'OK'

    #private
    def _error_handler_default(self):
        eh = ErrorHandler()
        eh.logger = self
        return eh

# ============= EOF ====================================
