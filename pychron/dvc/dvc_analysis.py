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
from pychron.processing.analyses.analysis import Analysis

ANALYSIS_ATTRS = ('labnumber', 'sample', 'aliquot', 'increment', 'irradiation', 'weight',
                  'comment', 'irradiation_level', 'mass_spectrometer', 'extract_device',
                  'username', 'tray', 'queue_conditionals_name', 'extract_value',
                  'extract_units', 'position', 'xyz_position', 'duration', 'cleanup',
                  'pattern', 'beam_diameter', 'ramp_duration', 'ramp_rate')


class DVCAnalysis(Analysis):
    def __init__(self, yd, *args, **kw):
        super(DVCAnalysis, self).__init__(*args, **kw)

        for attr in ANALYSIS_ATTRS:
            v = yd.get(attr)
            if v is not None:
                setattr(self, attr, v)

        self.rundate = yd['timestamp']  # datetime.strptime(yd['timestamp'], '%Y-%m-%dT%H:%M:%S')
        self.collection_version = yd['collection_version']

# ============= EOF =============================================



