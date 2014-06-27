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

#============= enthought library imports =======================
import os
import time

from traits.api import HasTraits

# ============= standard library imports ========================
# import re
#============= local library imports  ==========================
from pychron.experiment.utilities.identifier import make_runid


class GraphicalRecordView(object):
    __slots__ = ['uuid', 'rundate', 'timestamp', 'record_id', 'analysis_type',
                 'tag', 'project', 'sample', 'is_plateau_step']

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
        if meas is not None and meas.analysis_type:
            self.analysis_type = meas.analysis_type.name

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


class IsotopeRecordView(HasTraits):
    group_id = 0
    graph_id = 0
    mass_spectrometer = ''
    extract_device = ''
    analysis_type = ''
    uuid = ''
    sample = ''
    project = ''

    iso_fit_status = False
    blank_fit_status = False
    ic_fit_status = False
    flux_fit_status = False

    tag = ''
    temp_status = 0

    record_id = ''

    is_plateau_step = False
    identifier = ''

    meas_script_name = ''
    extract_script_name = ''

    status_text = ''

    def __init__(self, dbrecord=None, *args, **kw):
        super(IsotopeRecordView, self).__init__(*args, **kw)
        if dbrecord:
            self.create(dbrecord)

    def set_tag(self, tag):
        self.tag = tag.name

    def create(self, dbrecord):
        #        print 'asdfsadfsdaf', dbrecord, dbrecord.labnumber, dbrecord.uuid
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
                    self.project = sam.project.name.lower()

            irp = ln.irradiation_position
            if irp is not None:
                irl = irp.level
                ir = irl.irradiation
                self.irradiation_info = '{}{} {}'.format(ir.name, irl.name, irp.position)

            else:
                self.irradiation_info = ''

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
#============= EOF =============================================
