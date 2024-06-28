# ===============================================================================
# Copyright 2011 Jake Ross
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


class Globals(object):
    db_ca_file = None
    db_key_file = None
    db_cert_file = None
    cert_file = None
    verify_ssl = True
    prev_db_kind = None
    dev_pwd = "6e06f5d370baef1a115ae2f134fae22fbfbe79dc"  # Argon
    # use_shared_memory = False

    use_debug_logger = False
    # use_debug_logger = True

    open_logger_on_launch = True
    quit_on_last_window = False
    # force display flags
    show_warnings = True
    show_infos = True
    show_startup_results = True

    # using ipc_dgram is currently not working
    ipc_dgram = False

    ignore_initialization_warnings = False
    ignore_connection_warnings = False
    ignore_chiller_unavailable = False
    ignore_initialization_required = False
    ignore_initialization_questions = False
    ignore_shareable = False
    ignore_plugin_warnings = False

    video_test = False
    #    video_test = True
    # video_test_path = '/Users/ross/Sandbox/pos_err/diodefailsnapshot.jpg'
    #    video_test_path = '/Users/ross/Sandbox/snapshot002-6.662--8.572.jpg'
    #    video_test_path = '/Users/ross/Sandbox/watershed_test.jpg'
    # video_test_path = '/Users/ross/Sandbox/watershed_test2.jpg'
    video_test_path = "/Users/ross/Sandbox/snapshot002.jpg"
    #    video_test_path = '/Users/ross/Sandbox/snapshot003-fail.jpg'
    show_autocenter_debug_image = False
    #    show_autocenter_debug_image = True

    test_experiment_set = None
    #    test_experiment_set = '/Users/ross/Pychrondata_experiment/experiments/bar.txt'
    # use_ipc = False == embed the remote hardware servers into pychron
    # = True == an instance of RemoteHardwareServer must be launched
    use_message_len_checking = False
    use_ipc = True

    _test = False  # set test to 'true' when running tests

    experiment_debug = False
    experiment_savedb = True
    automated_run_debug = False
    spectrometer_debug = False
    system_monitor_debug = False
    # figure_debug = False
    # browser_debug = False
    auto_pipeline_debug = False
    skip_configure = False

    load_valve_states = True
    load_soft_locks = True
    load_manual_states = True

    debug = False
    use_logger_display = True
    use_warning_display = True
    # recall_debug = False
    pipeline_debug = False
    mdd_workspace_debug = False
    pipeline_template = None
    select_default_data = True
    run_pipeline = False

    valve_debug = False

    dev_confirm_exit = True
    username = "root"
    communication_simulation = False
    use_startup_tests = True
    dashboard_simulation = False
    use_testbot = False
    random_tip_enabled = True
    client_only_locking = True

    irradiation_pdf_debug = False
    entry_labbook_debug = False
    entry_irradiation_import_from_file_debug = False

    active_analyses = None
    active_branch = None

    own_spectrometer = None

    laser_version = 1

    def build(self, ip):
        for attr, func in [
            ("use_ipc", to_bool),
            ("ignore_plugin_warnings", to_bool),
            ("ignore_initialization_warnings", to_bool),
            ("ignore_connection_warnings", to_bool),
            ("ignore_chiller_unavailable", to_bool),
            ("ignore_initialization_required", to_bool),
            ("ignore_initialization_questions", to_bool),
            ("ignore_shareable", to_bool),
            ("show_startup_results", to_bool),
            ("show_infos", to_bool),
            ("show_warnings", to_bool),
            ("open_logger_on_launch", to_bool),
            ("quit_on_last_window", to_bool),
            ("video_test", to_bool),
            ("load_valve_states", to_bool),
            ("load_soft_locks", to_bool),
            ("load_manual_states", to_bool),
            ("experiment_debug", to_bool),
            ("experiment_savedb", to_bool),
            ("run_pipeline", to_bool),
            ("select_default_data", to_bool),
            ("pipeline_template", str),
            ("mdd_workspace_debug", to_bool),
            ("auto_pipeline_debug", to_bool),
            ("pipeline_debug", to_bool),
            # ('recall_debug', to_bool),
            # ('figure_debug', to_bool),
            # ('browser_debug', to_bool),
            ("skip_configure", to_bool),
            ("valve_debug", to_bool),
            ("communication_simulation", to_bool),
            ("dashboard_simulation", to_bool),
            ("use_startup_tests", to_bool),
            ("use_testbot", to_bool),
            ("dev_confirm_exit", to_bool),
            ("random_tip_enabled", to_bool),
            ("test_experiment_set", str),
            ("own_spectrometer", str),
            ("system_monitor_debug", to_bool),
            ("entry_labbook_debug", to_bool),
            ("irradiation_pdf_debug", to_bool),
            ("entry_irradiation_import_from_file_debug", to_bool),
            ("client_only_locking", to_bool),
            ("cert_file", str),
            ("db_cert_file", str),
            ("db_ca_file", str),
            ("db_key_file", str),
            ("laser_version", int),
            ("verify_ssl", to_bool),
        ]:
            a = ip.get_global(attr)
            if a is not None:
                setattr(globalv, attr, func(a))

    def _get_test(self):
        return self._test

    # mode is readonly. set once in the launchers/pychron.py module
    test = property(fget=_get_test)


globalv = Globals()

# ============= EOF =============================================
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
