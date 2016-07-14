# ===============================================================================
# Copyright 2014 Jake Ross
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
from pychron.core.ui import set_qt

set_qt()

# ============= enthought library reverts =======================
from traits.api import Any, Str
# ============= standard library imports ========================
import os
import struct
from numpy import array
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import pathtolist
from pychron.loggable import Loggable
from pychron.core.helpers.logger_setup import logging_setup
from pychron.mass_spec.database.massspec_database_adapter import MassSpecDatabaseAdapter
from pychron.database.isotope_database_manager import IsotopeDatabaseManager
from pychron.experiment.utilities.identifier import convert_identifier_to_int, strip_runid

logging_setup('ms_reverter')


class MassSpecReverter(Loggable):
    """
        use to revert data from Pychron to MassSpec.
        uses the MassSpecDatabasereverter to do the actual work.
        This class takes a list of run ids, extracts data from
        the pychron database, prepares data for use with MassSpecDatabasereverter,
        then writes to the MassSpec database

    """
    source = Any
    destination = Any
    path = Str

    def do_revert(self):
        # if self._connect_to_source():
        if self._connect_to_destination():
            self._do_revert()

    def do_reimport(self):
        if self._connect_to_source():
            if self._connect_to_destination():
                self._do_reimport()

    def setup_source(self):
        src = IsotopeDatabaseManager(connect=False, bind=False)
        db = src.db
        db.trait_set(name='pychrondata',
                     kind='mysql',
                     host=os.environ.get('HOST'),
                     username='root',
                     password=os.environ.get('DB_PWD'))
        self.source = src

    def setup_destination(self):
        dest = MassSpecDatabaseAdapter()
        dest.trait_set(name='massspecdata_crow',
                       kind='mysql',
                       username='root',
                       password=os.environ.get('DB_PWD'))
        self.destination = dest

    def _connect_to_source(self):
        return self.source.connect()

    def _connect_to_destination(self):
        return self.destination.connect()

    def _load_runids(self):
        runids = pathtolist(self.path)
        return runids

    def _do_reimport(self):
        rids = self._load_runids()
        for rid in rids:
            self._reimport_rid(rid)

    def _reimport_rid(self, rid):
        self.debug('========= Reimport {} ========='.format(rid))

        dest = self.destination
        src_an = self._get_analysis_from_source(rid)
        if src_an is None:
            self.warning('could not find {}'.format(rid))
        else:
            dest_an = dest.get_analysis_rid(rid)
            for iso in dest_an.isotopes:
                pb, pbnc = self._generate_blobs(src_an, iso.Label)
                pt = iso.peak_time_series[0]
                pt.PeakTimeBlob = pb
                pt.PeakNeverBslnCorBlob = pbnc
            dest.commit()

    def _generate_blobs(self, src, isok):
        dbiso = next((i for i in src.isotopes if i.molecular_weight.name == isok and i.kind == 'signal'), None)
        dbiso_bs = next((i for i in src.isotopes if i.molecular_weight.name == isok and i.kind == 'baseline'), None)

        xs, ys = self._unpack_data(dbiso.signal.data)
        bsxs, bsys = self._unpack_data(dbiso_bs.signal.data)
        bs = bsys.mean()
        cys = ys - bs

        ncblob = ''.join([struct.pack('>f', v) for v in ys])
        cblob = ''.join([struct.pack('>ff', y, x) for y, x in zip(cys, xs)])

        return cblob, ncblob

    def _unpack_data(self, blob):
        endianness = '>'
        sx, sy = zip(*[struct.unpack('{}ff'.format(endianness),
                                     blob[i:i + 8]) for i in xrange(0, len(blob), 8)])
        return array(sx), array(sy)

    def _get_analysis_from_source(self, rid):
        if rid.count('-') > 1:
            args = rid.split('-')
            step = None
            lan = '-'.join(args[:-1])
            aliquot = args[-1]
        else:
            lan, aliquot, step = strip_runid(rid)
            lan = convert_identifier_to_int(lan)

        db = self.source.db
        dban = db.get_unique_analysis(lan, aliquot, step)
        return dban

    def _do_revert(self):
        rids = self._load_runids()
        for rid in rids:
            self._revert_rid(rid)

    def _revert_rid(self, rid):
        """
            rid: str. typical runid e.g 12345, 12345-01, 12345-01A

            if rid lacks an aliquot revert all aliquots and steps for
            this rid
        """
        self.debug('reverting {}'.format(rid))
        if '-' in rid:
            # this is a specific analysis
            self._revert_analysis(rid)
        else:
            self._revert_analyses(rid)

    def _revert_analyses(self, rid):
        """
            rid: str. e.g 12345

            revert all analyses with this labnumber
        """

    def _revert_analysis(self, rid):
        """
            rid: str. e.g 12345-01 or 12345-01A
            only revert this specific analysis
        """
        # l,a,s = strip_runid(rid)
        # db = self.source.db
        dest = self.destination
        # with db.session_ctx():
        self.debug('========= Revert {} ========='.format(rid))
        dest_an = dest.get_analysis_rid(rid)
        for iso in dest_an.isotopes:
            isol = iso.Label
            self.debug('{} reverting isotope id = {}'.format(isol, iso.IsotopeID))

            # fix IsotopeTable.NumCnts
            n = len(iso.peak_time_series[0].PeakTimeBlob) / 8
            self.debug('{} fixing NumCnts. current={} new={}'.format(isol, iso.NumCnts, n))
            iso.NumCnts = n

            nf = len(iso.peak_time_series)
            if nf > 1:
                self.debug('{} deleting {} refits'.format(isol, nf - 1))
                # delete peak time blobs
                for i, pt in enumerate(iso.peak_time_series[1:]):
                    self.debug('{} A {:02d} deleting pt series {}'.format(isol, i + 1, pt.Counter))
                    dest.delete(pt)

                # delete isotope results
                for i, ir in enumerate(iso.results[1:]):
                    self.debug('{} B {:02d} deleting results {}'.format(isol, i + 1, ir.Counter))
                    dest.delete(ir)

        dest.commit()

if __name__ == '__main__':
    m = MassSpecReverter(path='/Users/ross/Sandbox/crow_revert.txt')
    m.setup_source()
    m.setup_destination()
    m.do_reimport()
    # m.do_revert()


# ============= EOF =============================================

#
# def _get_analyses_from_source(self, labnumber):
# db = self.source.db
# with db.session_ctx():
#         pass
