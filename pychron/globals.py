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
from pychron.helpers.filetools import to_bool


class Globals(object):
    # use_shared_memory = False

    use_debug_logger = False
    # use_debug_logger = True

    open_logger_on_launch = True

    # force display flags
    show_warnings = True
    show_infos = True

    # using ipc_dgram is currently not working
    ipc_dgram = False

    ignore_initialization_warnings = False
    ignore_connection_warnings = False
    ignore_chiller_unavailable = False
    ignore_required = False
    ignore_initialization_questions = False

    video_test = False
    #    video_test = True
    video_test_path = '/Users/ross/Sandbox/pos_err/diodefailsnapshot.jpg'
    #    video_test_path = '/Users/ross/Sandbox/snapshot002-6.662--8.572.jpg'
    #    video_test_path = '/Users/ross/Sandbox/watershed_test.jpg'
    video_test_path = '/Users/ross/Sandbox/watershed_test2.jpg'
    video_test_path = '/Users/ross/Sandbox/snapshot002.jpg'
    #    video_test_path = '/Users/ross/Sandbox/snapshot003-fail.jpg'
    show_autocenter_debug_image = False
    #    show_autocenter_debug_image = True

    test_experiment_set = None
    #    test_experiment_set = '/Users/ross/Pychrondata_experiment/experiments/bar.txt'
    # use_ipc = False == embed the remote hardware servers into pychron
    # = True == an instance of RemoteHardwareServer must be launched

    use_ipc = False

    _test = False  # set test to 'true' when running tests

    experiment_debug = False
    #    experiment_debug = True
    experiment_savedb = True
    automated_run_debug = False
    spectrometer_debug = False
    #    spectrometer_debug = True

    load_valve_states = True
    load_soft_locks = True

    debug = False

    def build(self, ip):

        for attr, func in [('use_ipc', to_bool),
                           ('ignore_initialization_warnings', to_bool),
                           ('ignore_connection_warnings', to_bool),
                           ('ignore_chiller_unavailable', to_bool),
                           ('ignore_required', to_bool),
                           ('ignore_initialization_questions', to_bool),
                           ('show_infos', to_bool),
                           ('show_warnings', to_bool),
                           ('video_test', to_bool),
                           ('load_valve_states', to_bool),
                           ('load_soft_locks', to_bool),
                           ('experiment_debug', to_bool),
                           ('experiment_savedb', to_bool),
                           ('test_experiment_set', str)
        ]:
            a = ip.get_global(attr)
            if a:
                setattr(globalv, attr, func(a))

    def _get_test(self):
        return self._test

    # mode is readonly. set once in the launchers/pychron.py module
    test = property(fget=_get_test)


globalv = Globals()

# class Globals():
#    _use_ipc = True
#    def get_use_ipc(self):
#        return self._use_ipc
#
#    def set_use_ipc(self, v):
#        self._use_ipc = v
#
#    use_ipc = property(fget=get_use_ipc,
#                     fset=set_use_ipc
#                     )
#
#
#
# global_obj = Globals()
# use_ipc = global_obj.use_ipc

