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

from traits.api import (
    HasTraits,
    Str,
    Int,
    Bool,
    Any,
    Float,
    Dict,
    Instance,
    List,
    Date,
    Time,
    Long,
    Bytes,
    Tuple,
)


# ============= standard library imports ========================
# ============= local library imports  ==========================


class PersistenceSpec(HasTraits):
    run_spec = Instance("pychron.experiment.automated_run.spec.AutomatedRunSpec")
    monitor = Instance("pychron.monitors.automated_run_monitor.AutomatedRunMonitor")
    isotope_group = Instance("pychron.processing.isotope_group.IsotopeGroup")

    auto_save_detector_ic = Bool
    signal_fods = Dict
    baseline_fods = Dict

    save_as_peak_hop = Bool(False)
    experiment_type = Str
    experiment_id = Int
    sensitivity_multiplier = Float
    experiment_queue_name = Str
    experiment_queue_blob = Str
    instrument_name = Str
    laboratory = Str

    extraction_name = Str
    extraction_blob = Str
    measurement_name = Str
    measurement_blob = Str

    post_measurement_name = Str
    post_measurement_blob = Str
    post_equilibration_name = Str
    post_equilibration_blob = Str

    hops_name = Str
    hops_blob = Str

    positions = List  # list of position names
    extraction_positions = List  # list of x,y or x,y,z tuples

    # for saving to mass spec
    runscript_name = Str
    runscript_blob = Str

    settings = Dict
    spec_dict = Dict
    defl_dict = Dict
    gains = Dict
    trap = Float
    emission = Float
    active_detectors = List

    baseline_modifiers = Dict
    modified_baselines = Dict

    previous_blank_runid = Str
    previous_blank_id = Long
    previous_blanks = Dict

    rundate = Date
    runtime = Time
    # load_name = Str
    # load_holder = Str

    cdd_ic_factor = Any

    whiff_result = None
    timestamp = None
    use_repository_association = True
    tag = "ok"
    peak_center = None
    intensity_scalar = 1.0

    pid = Str
    response_blob = Bytes
    output_blob = Bytes
    setpoint_blob = Bytes
    cryo_response_blob = Bytes
    snapshots = List
    videos = List
    extraction_context = Dict

    conditionals = List
    tripped_conditional = None

    grain_polygons = List

    power_achieved = Float
    lab_temperatures = List
    lab_humiditys = List
    lab_pneumatics = List

    pipette_counts = List
    time_zero = Float
    # lithographic_unit = Str
    # lat_long = Str
    # rock_type = Str
    # reference = Str


# ============= EOF =============================================
