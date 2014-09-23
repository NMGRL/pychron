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


class GraphicalRecordView(object):
    __slots__ = ['uuid', 'rundate', 'timestamp', 'record_id', 'analysis_type',
                 'tag', 'project', 'sample', 'is_plateau_step', 'mass_spectrometer']

    def __init__(self, dbrecord):
        self.uuid = dbrecord.uuid
        ln = dbrecord.labnumber
        labnumber = str(ln.identifier)
        aliquot = dbrecord.aliquot
        step = dbrecord.step
        self.record_id = make_runid(labnumber, aliquot, step)

        self.rundate = dbrecord.analysis_timestamp
        self.timestamp = time.mktime(self.rundate.timetuple())
        self.tag = dbrecord.tag or ''
        self.is_plateau_step = False

        meas = dbrecord.measurement
        if meas is not None:
            if meas.analysis_type:
                self.analysis_type = meas.analysis_type.name
            if meas.mass_spectrometer:
                self.mass_spectrometer = meas.mass_spectrometer.name

        sam = ln.sample
        if sam:
            self.sample = sam.name
            if sam.project:
                self.project = sam.project.name.lower()


def get_flux_fit_status(item):
    labnumber = item.labnumber
    return 'X' if labnumber.selected_flux_id else ''


def get_selected_history_item(item, key):
    sh = item.selected_histories
    return ('X' if getattr(sh, key) else '') if sh else ''


class IsotopeRecordView(object):
    __slots__ = ('sample', 'project', 'labnumber', 'identifier', 'aliquot', 'step', 'record_id', 'uuid', 'rundate',
                 'timestamp', 'tag', 'irradiation_info', 'mass_spectrometer', 'analysis_type',
                 'meas_script_name', 'extract_script_name', 'extract_device', 'flux_fit_status',
                 'blank_fit_status',
                 'ic_fit_status',
                 'iso_fit_status', 'is_plateau_step', 'group_id', 'graph_id')

    def __init__(self, dbrecord=None, *args, **kw):
        self.is_plateau_step = False
        self.extract_script_name = ''
        self.meas_script_name = ''
        self.analysis_type = ''
        self.group_id = 0
        self.graph_id = 0

        self.identifier = ''
        self.labnumber = ''
        self.aliquot = 0
        self.step = ''
        self.tag = ''
        self.uuid = ''
        self.rundate = ''
        self.timestamp = ''
        self.record_id = ''
        self.sample = ''
        self.project = ''
        self.irradiation_info = ''
        self.mass_spectrometer = ''
        self.extract_device = ''

        self.flux_fit_status = ''
        self.blank_fit_status = ''
        self.ic_fit_status = ''
        self.iso_fit_status = ''

        super(IsotopeRecordView, self).__init__(*args, **kw)

        if dbrecord:
            self.create(dbrecord)

    def set_tag(self, tag):
        self.tag = tag.name

    def create(self, dbrecord):
        # print 'asdfsadfsdaf', dbrecord, dbrecord.labnumber, dbrecord.uuid
        try:
            if dbrecord is None or not dbrecord.labnumber:
                return

            ln = dbrecord.labnumber

            self.labnumber = str(ln.identifier)
            self.identifier = self.labnumber

            self.aliquot = dbrecord.aliquot
            self.step = dbrecord.step
            self.uuid = dbrecord.uuid
            self.tag = dbrecord.tag or ''
            self.rundate = dbrecord.analysis_timestamp

            self.timestamp = time.mktime(self.rundate.timetuple())
            self.record_id = make_runid(self.labnumber, self.aliquot, self.step)

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
            if meas is not None:
                self.mass_spectrometer = meas.mass_spectrometer.name.lower()
                if meas.script:
                    self.meas_script_name = self._clean_script_name(meas.script.name)
                if meas.analysis_type:
                    self.analysis_type = meas.analysis_type.name
            ext = dbrecord.extraction
            if ext:
                if ext.script:
                    self.extract_script_name = self._clean_script_name(ext.script.name)
                if ext.extraction_device:
                    self.extract_device = ext.extraction_device.name

            self.flux_fit_status = get_flux_fit_status(dbrecord)
            self.blank_fit_status = get_selected_history_item(dbrecord, 'selected_blanks_id')
            self.ic_fit_status = get_selected_history_item(dbrecord, 'selected_det_intercal_id')
            self.iso_fit_status = get_selected_history_item(dbrecord, 'selected_fits_id')

            return True
        except Exception, e:
            import traceback

            traceback.print_exc()
            print e

    def _clean_script_name(self, name):
        n = name.replace('{}_'.format(self.mass_spectrometer.lower()), '')
        n, t = os.path.splitext(n)
        return n

    def to_string(self):
        return '{} {} {} {}'.format(self.labnumber, self.aliquot, self.timestamp, self.uuid)

# ============= EOF =============================================
