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



# =============enthought library imports========================

# ============= standard library imports =======================
# ============= local library imports  =========================
from pychron.remote_hardware.errors import ManagerUnavaliableErrorCode, \
    InvalidCommandErrorCode, NoResponseErrorCode, FuncCallErrorCode
from pychron.remote_hardware.errors.error import ErrorCode
# from pychron.loggable import Loggable


class ErrorHandler:
    logger = None

    def check_manager(self, manager, name):
        if manager is None:
            return ManagerUnavaliableErrorCode(name, logger=self.logger)

    def check_command(self, handler, args):
        if args:

            command_func = handler.get_func(args[0])
            if command_func is None:
                return InvalidCommandErrorCode(args[0], logger=self.logger), None
            else:
                return None, command_func
        else:
            return InvalidCommandErrorCode(None, logger=self.logger), None

    def check_response(self, func, manager, args):
        """
            performs the requested command and checks for errors
        """
        result = None
        err = None
        try:
            result = func(manager, *args)

            if result is None:
                err = NoResponseErrorCode(logger=self.logger)
            elif isinstance(result, ErrorCode):
                err = result

        except TypeError, e:
            import traceback
            traceback.print_exc()
            err = FuncCallErrorCode(e, args, logger=self.logger)

        return err, '{}'.format(str(result))

if __name__ == '__main__':
    ec = ErrorHandler()

# ============= EOF ============================================
