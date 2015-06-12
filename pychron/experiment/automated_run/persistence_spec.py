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
from traits.api import HasTraits, Str, Int, Bool, Any, Float, \
    Dict, Instance, List, Date, Time, Long
# ============= standard library imports ========================
# ============= local library imports  ==========================


class PersistenceSpec(HasTraits):
    run_spec = Instance('pychron.experiment.automated_run.spec.AutomatedRunSpec')
    monitor = Instance('pychron.monitors.automated_run_monitor.AutomatedRunMonitor')
    arar_age = Instance('pychron.processing.arar_age.ArArAge')

    auto_save_detector_ic = Bool
    signal_fods = Dict
    baseline_fods = Dict

    save_as_peak_hop = Bool(False)
    experiment_identifier = Int
    sensitivity_multiplier = Float
    experiment_queue_name = Str
    experiment_queue_blob = Str

    extraction_name = Str
    extraction_blob = Str
    measurement_name = Str
    measurement_blob = Str
    positions = List  # list of position names
    extraction_positions = List  # list of x,y or x,y,z tuples

    # for saving to mass spec
    runscript_name = Str
    runscript_blob = Str

    spec_dict = Dict
    defl_dict = Dict
    gains = Dict

    active_detectors = List

    previous_blank_runid = Str
    previous_blank_id = Long
    previous_blanks = Dict

    rundate = Date
    runtime = Time
    load_name = Str

    cdd_ic_factor = Any

    whiff_result = None
    timestamp = None
    use_experiment_association = False
# ============= EOF =============================================
