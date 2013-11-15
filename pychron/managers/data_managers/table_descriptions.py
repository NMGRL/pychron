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



# @PydevCodeAnalysisIgnore

#============= enthought library imports =======================

#============= standard library imports ========================
from tables import Float32Col, StringCol, IsDescription
#============= local library imports  ==========================

class TimeSeriesTableDescription(IsDescription):
    time = Float32Col()
    value = Float32Col()


class CameraScanTableDescription(IsDescription):
    """
    """
    setpoint = Float32Col()
    frame_path = StringCol(140)
    ravg = Float32Col()
    gavg = Float32Col()
    bavg = Float32Col()

    # tc_temp=Float32Col()


class DiodePowerScanTableDescription(IsDescription):
    """
    """
    setpoint = Float32Col()
    eq_time = Float32Col()


class TimestampTableDescription(IsDescription):
    """

    """
    timestamp = StringCol(24)
    value = Float32Col()


class PowerScanTableDescription(IsDescription):
    """

    """
    power_requested = Float32Col()
    power_achieved = Float32Col()
    voltage = Float32Col()


class PowerMapTableDescription(IsDescription):
    """

    """
    row = Float32Col()
    col = Float32Col()
    x = Float32Col()
    y = Float32Col()
    power = Float32Col()


class AnalysesTableDescription(IsDescription):
    time = Float32Col()
    y = Float32Col()


class PowerCalibrationTableDescription(IsDescription):
    setpoint = Float32Col()
    value = Float32Col()


def table_description_factory(table_name):
    """
    """
    n = '{}TableDescription'.format(table_name)
    return globals()[n]

#============= EOF ====================================
