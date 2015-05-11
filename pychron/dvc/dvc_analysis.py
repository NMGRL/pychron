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
import time
# ============= local library imports  ==========================
from pychron.processing.analyses.analysis import Analysis

ANALYSIS_ATTRS = ('labnumber', 'sample', 'project', 'material', 'aliquot', 'increment', 'irradiation', 'weight',
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

    def set_chronology(self, chron):
        analts = self.rundate

        convert_days = lambda x: x.total_seconds() / (60. * 60 * 24)
        doses = chron.get_doses()
        segments = [(pwr, convert_days(en - st), convert_days(analts - st))
                    for pwr, st, en in doses
                    if st is not None and en is not None]

        d_o = doses[0][1]
        self.irradiation_time = time.mktime(d_o.timetuple()) if d_o else 0
        self.chron_segments = segments
        self.chron_dosages = doses
        self.calculate_decay_factors()

# ============= EOF =============================================



