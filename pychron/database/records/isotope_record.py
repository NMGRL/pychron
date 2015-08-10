# ===============================================================================
# Copyright 2012 Jake Ross
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
import os
import time

# ============= standard library imports ========================
# import re
# ============= local library imports  ==========================
from pychron.experiment.utilities.identifier import make_runid
from pychron.pychron_constants import ALPHAS


# class GraphicalRecordView(object):
# __slots__ = ['uuid', 'rundate', 'timestamp', 'record_id', 'analysis_type',
#                  'tag', 'project', 'sample', 'is_plateau_step', 'mass_spectrometer']
#
#     def __init__(self, dbrecord):
#         self.uuid = dbrecord.uuid
#         ln = dbrecord.labnumber
#         labnumber = str(ln.identifier)
#         aliquot = dbrecord.aliquot
#         step = dbrecord.step
#         self.record_id = make_runid(labnumber, aliquot, step)
#
#         self.rundate = dbrecord.analysis_timestamp
#         self.timestamp = time.mktime(self.rundate.timetuple())
#         self.tag = dbrecord.tag or ''
#         self.is_plateau_step = False
#
#         meas = dbrecord.measurement
#         if meas is not None:
#             if meas.analysis_type:
#                 self.analysis_type = meas.analysis_type.name
#             if meas.mass_spectrometer:
#                 self.mass_spectrometer = meas.mass_spectrometer.name
#
#         sam = ln.sample
#         if sam:
#             self.sample = sam.name
#             if sam.project:
#                 self.project = sam.project.name.lower()


def get_flux_fit_status(item):
    labnumber = item.labnumber
    return 'X' if labnumber.selected_flux_id else ''


def get_selected_history_item(sh, key):
    # sh = item.selected_histories
    return ('X' if getattr(sh, key) else '') if sh else ''


# class IsotopeRecordView(object):
#     pass


#
class IsotopeRecordView(object):
    __slots__ = ('sample', 'project', 'labnumber', 'identifier', 'aliquot', 'step',
                 '_increment',
                 'uuid', 'rundate',
                 'timestampf', 'tag',
                 'delta_time',
                 'tag_dict',
                 'irradiation_position_position',
                 'irradiation', 'irradiation_level',
                 'irradiation_info', 'mass_spectrometer', 'analysis_type',
                 'meas_script_name', 'extract_script_name', 'extract_device', 'flux_fit_status',
                 'extract_value', 'cleanup', 'duration',
                 'blank_fit_status',
                 'ic_fit_status',
                 'experiment_identifier',
                 'experiment_ids',
                 'iso_fit_status', 'is_plateau_step', 'group_id', 'graph_id')

    def __init__(self, *args, **kw):
        self.is_plateau_step = False
        self.extract_script_name = ''
        self.meas_script_name = ''
        self.analysis_type = ''
        self.group_id = 0
        self.graph_id = 0

        self.identifier = ''
        self.labnumber = ''
        self.aliquot = 0
        self._increment = -1
        self.step = ''
        self.tag = ''
        self.tag_dict = None
        self.uuid = ''
        self.experiment_identifier = ''
        self.experiment_ids = None
        self.rundate = ''
        self.timestampf = 0
        self.delta_time = 0
        # self.record_id = ''
        self.sample = ''
        self.project = ''
        self.irradiation_info = ''
        self.irradiation = ''
        self.irradiation_level = ''
        self.irradiation_position_position = ''
        self.mass_spectrometer = ''
        self.extract_device = ''

        self.flux_fit_status = ''
        self.blank_fit_status = ''
        self.ic_fit_status = ''
        self.iso_fit_status = ''

        self.extract_value = 0
        self.cleanup = 0
        self.duration = 0

        # super(IsotopeRecordView, self).__init__(*args, **kw)

    def set_tag(self, tag):
        self.tag = tag.name

    def create(self, dbrecord, fast_load=False):
        # print 'asdfsadfsdaf', dbrecord, dbrecord.labnumber, dbrecord.uuid
        try:
            if dbrecord is None or not dbrecord.labnumber:
                return

            ln = dbrecord.labnumber

            self.labnumber = str(ln.identifier)
            self.identifier = self.labnumber

            self.aliquot = dbrecord.aliquot
            self.step = dbrecord.step
            self._increment = dbrecord.increment
            # temporary hack to handle increment
            # todo: change database so all increment=-1 where step=''
            # change how automated run persister sets increment
            if not self.step:
                self._increment = -1

            # self.record_id = make_runid(self.labnumber, self.aliquot, self.step)

            self.uuid = dbrecord.uuid
            self.tag = dbrecord.tag or ''
            self.rundate = dbrecord.analysis_timestamp

            sam = ln.sample
            if sam:
                self.sample = sam.name
                if sam.project:
                    if isinstance(sam.project, (str, unicode)):
                        self.project = sam.project.lower()
                    else:
                        self.project = sam.project.name.lower()

            irp = ln.irradiation_position
            if irp is not None:
                irl = irp.level
                ir = irl.irradiation
                self.irradiation_info = '{}{} {}'.format(ir.name, irl.name, irp.position)

            try:
                self.mass_spectrometer = dbrecord.mass_spectrometer
            except AttributeError:
                pass

            meas = dbrecord.measurement
            if meas:
                self.mass_spectrometer = meas.mass_spectrometer.name.lower()
                try:
                    self.analysis_type = meas.analysis_type.name
                except AttributeError, e:
                    pass
                    # print 'IsotopeRecord create meas 1 {}'.format(e)

            ext = dbrecord.extraction
            if ext:
                self.extract_value = ext.extract_value
                self.cleanup = ext.cleanup_duration
                self.duration = ext.extract_duration

                try:
                    if ext.extraction_device:
                        self.extract_device = ext.extraction_device.name
                except AttributeError, e:
                    pass
                    # print 'IsotopeRecord create ext 2 {}'.format(e)

            if not fast_load:
                self.timestamp = time.mktime(self.rundate.timetuple())
                if meas:
                    try:
                        self.meas_script_name = self._clean_script_name(meas.script.name)
                    except AttributeError, e:
                        pass
                        # print 'IsotopeRecord create meas 2 {}'.format(e)
                else:
                    print 'measurment is None'

                if ext is not None:
                    try:
                        self.extract_script_name = self._clean_script_name(ext.script.name)
                    except AttributeError, e:
                        pass
                        # print 'IsotopeRecord create ext 1 {}'.format(e)
                else:
                    print 'extraction is None'

                self.flux_fit_status = get_flux_fit_status(dbrecord)

                sh = dbrecord.selected_histories
                self.blank_fit_status = get_selected_history_item(sh, 'selected_blanks_id')
                self.ic_fit_status = get_selected_history_item(sh, 'selected_det_intercal_id')
                self.iso_fit_status = get_selected_history_item(sh, 'selected_fits_id')

            return True
        except Exception, e:
            import traceback

            traceback.print_exc()
            print e

    def _clean_script_name(self, name):
        n = name.replace('{}_'.format(self.mass_spectrometer.lower()), '')
        n = os.path.basename(n)
        n, t = os.path.splitext(n)
        return n

    def to_string(self):
        return '{} {} {} {}'.format(self.identifier, self.aliquot, self.timestamp, self.uuid)

    @property
    def record_id(self):
        return make_runid(self.identifier, self.aliquot, self.step)

    @property
    def increment(self):
        return self._increment

    @increment.setter
    def increment(self, v):
        if v >= 0:
            self._increment = v
            self.step = ALPHAS[v]
        else:
            self._increment = -1
            self.step = ''

# ============= EOF =============================================
