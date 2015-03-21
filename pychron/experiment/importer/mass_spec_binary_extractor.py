# ===============================================================================
# Copyright 2013 Jake Ross
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
# ===============================================================================

# ============= enthought library imports =======================
#from pychron.processing.extractor.extractor import Extractor
import os
import struct
# ============= standard library imports ========================
# ============= local library imports  ==========================
from datetime import datetime
from pychron.experiment.importer.extractor import Extractor


class BinarySpec(object):
    pass


class MeasurementObject(object):
    name=''
    xs=None
    ys=None
    ncnts=0

class Baseline(MeasurementObject):
    pass

class Isotope(MeasurementObject):
    pass


class MassSpecBinaryExtractor(Extractor):
    def _get_next_str(self, fp):
        def _gen():
            t = ''
            while 1:
                a = fp.read(1)
                if a == '\t':
                    yield t.strip()
                    t = ''
                t += a

        g = _gen()
        return lambda: g.next()

    def _get_single(self, fp):
        def _gen():
            t = struct.unpack('>f', fp.read(4))[0]
            return t

        return _gen

    def _get_short(self, fp):
        def _gen():
            t = struct.unpack('>h', fp.read(2))[0]
            return t

        return _gen

    def _get_long(self, fp):
        def _gen():
            t = struct.unpack('>l', fp.read(4))[0]
            return t

        return _gen

    def _get_double(self, fp):
        def _gen():
            t = struct.unpack('>d', fp.read(8))[0]
            return t

        return _gen

    def import_file(self, p):
        """
            clone of RunData.Binary_Read from MassSpec 7.875
        """
        if not os.path.isfile(p):
            return

        bs = []
        with open(p, 'r') as fp:
            while 1:
                try:
                    bs.append(self._import_analysis(fp))
                except EOFError:
                    pass
                break

        return bs

    def _import_analysis(self, fp):
        isref, isblank = False, False

        bspec = BinarySpec()

        # use big-endian
        gns = self._get_next_str(fp)

        gshort = self._get_short(fp)
        gsingle = self._get_single(fp)
        glong = self._get_long(fp)
        gdouble = self._get_double(fp)

        bspec.runid = gns()

        ms_data_file_ver = 7.875
        if ms_data_file_ver < 7.875:
            ignored_rid = gns()

        bspec.sample = gns()
        bspec.material = gns()
        bspec.investigator = gns()
        bspec.project = gns()
        bspec.locality = gns()
        bspec.rundate = gns()
        bspec.runday = self._calculate_days(bspec.rundate)
        bspec.irradlabel = gns()
        bspec.fits = gns()
        bspec.comment = gns()
        bspec.runhour = gsingle()

        gof1, gof1 = gsingle(), gsingle()
        emv = [gsingle()]
        bspec.optemp = gsingle()

        bspec.version = ver = gsingle()

        if ver > 4.96:
            emv.append(gsingle())

        bspec.emv = emv

        if ver >= 4.6:
            bspec.history = gns()

        if ver >= 2:
            s1 = gsingle()
        else:
            s1 = 0  #10  10

        bspec.scalefactor = s1, s1
        bspec.extract_device = gns() if ver >= 4.46 else ''

        extract_value = gsingle()
        fsp = extract_value
        if ver > 3.1:
            fsp = gsingle()  # final set power

        bspec.extract_value = extract_value  #power achieved
        bspec.final_set_power = fsp  #power requested
        #
        # if extract_value == 0:
        #     if fsp > 0:
        #         extract_value = fsp
        #     elif not (isref or isblank):
        #         extract_value = float(comment)
        #
        bspec.totdur_heating = glong() if ver > 4.34 else 0
        bspec.totdur_atsetpoint = glong() if ver > 4.34 else 0

        gain = []
        if ver > 2.32:
            gain.append(gsingle())

        if ver > 4.96:
            gain.append(gsingle())

        bspec.gain = gain

        bspec.calc_with_ratio = bool(gshort())

        system_number = 1
        mol_ref_iso = 0
        if ver > 2.33:
            mol_ref_iso = gsingle()
            mol_ref_iso_special = mol_ref_iso < 0
            mol_ref_iso = abs(mol_ref_iso)
            system_number = gshort()
            if bspec.runday<1800:
                system_number=1

        bspec.mol_ref_iso = mol_ref_iso
        bspec.system_number = system_number

        disc_source = 3
        disc = 0
        disc_err = 0
        j = 0
        j_err = 0
        if ver > 2.992:
            disc = gsingle()
            disc_err = gsingle()
            j = gsingle()
            j_err = gsingle()
            disc_source = 2

        bspec.disc = disc
        bspec.disc_err = disc_err
        bspec.j = j
        bspec.j_err = j_err

        resistor_values = [1, 1, 10 ** 11]
        if ver > 4.02:
            resistor_values[2] = gsingle()
            resistor_values[0] = gsingle()
            if ver > 4.96:
                resistor_values[1] = gsingle()
            if isref:
                mol_ref_iso = gsingle()

        bspec.resistor_values = resistor_values
        isogrp = 'Ar'
        if ver > 6.67 and ver < 7.245:
            isogrp = gns()
        elif ver >= 7.245:
            dum = gshort()
        elif ver > 2.93 and ver < 6.67:
            grps = 'He,Ar,Ne,Kr,Xe'.split(',')

            # Mass Spec is 1-indexed
            idx = gshort() - 1

            isogrp = grps[idx]

        bspec.isogrp = isogrp

        niso = gshort() if ver > 2.96 else 5
        nratio = gshort() if ver > 2.98 else 4

        if ver > 2.92:
            if ver < 3.1:
                _, x = gsingle(), gsingle()

            dets = []
            for i in range(niso):
                dt = gshort()
                if dt == 0:
                    dt = 1
                dets.append(dt)
        else:
            dets = [1, ] * niso

        bspec.detectors = dets
        ndet = 1
        if ver >= 3.81:
            ndet = gshort()
            if ndet > 1:
                mx_det_type_n = 1
                #                     det_conv_factor = []
                for i in range(mx_det_type_n):
                    for j in range(i, mx_det_type_n, 1):
                        gsingle()

        elif ver >= 3.1:
            ndet = gshort()
            if ndet > 1:
                for i in range(ndet):
                    for j in range(ndet):
                        gsingle()

        # bspec.detector_ics =
        bspec.ndet = ndet

        bspec.refdetnum = gshort() or 1 if ver > 4.02 else 1

        if 2.994 < ver < 3.1:
            gsingle()

        bspec.signormfactor = gsingle() if ver > 4 else 1

        bspec.ncyc = gshort() if ver > 2.994 else -1

        if ver > 2.994:
            isokeys = []
            for i in range(niso + nratio):
                t = gns().replace(' ', '')
                isokeys.append(t)
            if ver > 3.121 and isref:
                if isokeys[1] == 'Ar40':
                    isokeys[1] = 'Ar39'
                if isokeys[2] == 'Ar40':
                    isokeys[2] = 'Ar38'

            if ver < 6 and isokeys[0].index('40'):
                isokeys[0] = 'Ar40'

            numisokeys = []
            demisokeys = []
            for i in range(nratio):
                numisokeys.append(gshort())
                demisokeys.append(gshort())

        else:
            niso = 5
            nratio = 4
            isokeys = ['Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36',
                       'Ar40/Ar39',
                       'Ar38/Ar39',
                       'Ar37/Ar39',
                       'Ar36/Ar39',
                       'Bsln']
            numisokeys = [0, 2, 3, 4]
            demisokeys = [1, 1, 1, 1]
            if isref:
                isokeys[5] = 'Ar40/Ar36'
                isokeys[6] = 'Ar40/Ar38'
                numisokeys = [1, 1, None, None]
                demisokeys = [5, 3, None, None]

        bspec.niso = niso
        bspec.nratio = nratio
        bspec.isokeys = isokeys

        ncnts = []
        isobsln = []
        for i in range(niso):
            ncnts.append(int(gshort()))

        isotopes = []
        for i in range(niso):
            iso, v = self._extract_isotope(ver, bspec.runday, ncnts[i], gsingle, gshort)
            isotopes.append(iso)
            isobsln.append(v)
        bspec.ncnts=ncnts
        bspec.isotopes=isotopes

        if bspec.calc_with_ratio:
            self._extract_ratios(ver, bspec, gsingle)

        self._extract_deleted_points(ver, bspec, gshort)
        if bspec.runday>515 and ver>1 and ver<2.995:
            x=gsingle()

        self._extract_baselines(ver, bspec, gns, gshort, gsingle, glong, gdouble)
        return bspec

    def _extract_baselines(self, ver, bspec, gns, gshort, gsingle, glong, gdouble):
        bspec.baselines=[]
        if bspec.runday>545.67 and ver>1.03:
            if ver>2.994:
                n=gshort()
                for i in xrange(int(n)):
                    label=gns()
                    bs = self._extract_baseline1(label, gshort, gsingle, gdouble)
                    bspec.baselines.append(bs)
            else:
                self._extract_baseline2(ver,gshort, gsingle, glong)

        self._extract_baseline_data(bspec, gsingle)

    def _extract_baseline_data(self, bspec, gsingle):
        for bs in bspec.baselines:
            xs,ys = self._extract_data(bs.ncnts, gsingle)
            bs.xs,bs.ys=xs,ys

    def _extract_baseline2(self, ver, gshort, gsingle, glong):
        ncnts=gshort()
        if ver>2.68:
            fit=gshort()
            nsegments=gshort()
            intercept=gsingle()
            intercept_err=gsingle()
            for i in xrange(4):
                for j in xrange(nsegments):
                    glong()
            for i in xrange(nsegments):
                glong()
        else:
            intercept=gsingle()
            slope = gsingle()
            if ver>2.0999:
                intercept_err=0 if ver<2.67 else gsingle()
        return ncnts

    def _extract_baseline1(self, label, gshort, gsingle, gdouble):
        baseline=Baseline()
        baseline.label=label
        ncnts = gshort()
        nRpts = gshort()
        npos = gshort()
        for i in xrange(npos):
            gsingle()

        nsegments=gshort()
        for i in xrange(nsegments):
            gsingle()
            for j in xrange(4):
                gdouble()
            gsingle()

        baseline.ncnts=ncnts
        return baseline

    def _extract_deleted_points(self, ver, bspec, gshort):
        if ver>2.61:
            niso, nratio=bspec.niso, bspec.nratio
            for i in xrange(gshort()):
                j=gshort()
                k=gshort()
                # if j>niso+nratio:
                #     j=j-niso-nratio

    def _extract_ratios(self,ver, bspec, gsingle):
        for i in xrange(bspec.nratio):
            if not (ver<2.41 and i==1):
                b=gsingle()
                c=gsingle()

    def _extract_isotope(self, ver, runday, ncnts, gsingle, gshort):
        """
        """

        isodict = {'background': gsingle(),
                   'background_err': gsingle(),
                   'intercept': gsingle(),
                   'intercept_err': gsingle()}
        xs, ys = self._extract_data(ncnts, gsingle)
        isodict['xs']=xs
        isodict['ys']=ys
        isodict['peak_height_change_percent'] = gsingle() if ver > 2.18 else 0
        bsln_n = 0
        c = -1
        if ver > 2.994:
            bsln_n = gshort()
            if runday<=543:
                bsln_n=0
            c = gshort()

        isodict['counts_per_cycle'] = c

        if runday>545.67 and ver>1.03:
            bsln_n=max(bsln_n, 1)
        return isodict, bsln_n

    def _extract_data(self, ncnts, gs):
        xs,ys=[],[]
        for i in xrange(ncnts):
            ys.append(gs())
            xs.append(gs())

        return xs,ys

    def _calculate_days(self, rundate_str):
        d=datetime.strptime(rundate_str, '%m/%d/%Y')
        refdate=datetime(year=1987, month=1, day=1)

        return (d-refdate).total_seconds()/86400.


# ============= EOF =============================================
