#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
#from pychron.processing.extractor.extractor import Extractor
import os
import struct
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.experiment.importer.extractor import Extractor


class MassSpecBinaryExtractor(Extractor):
    def _get_next_str(self, fp):
        def _gen():
            while 1:
                t = ''
                while 1:
                    a = fp.read(1)
                    if a == '\t':
                        yield t.strip()
                        t = ''
                    t += a

        g = _gen()
        return lambda: g.next()

    #         return lambda :_gen()

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

    def import_file(self, p):
        if not os.path.isfile(p):
            return

        isref, isblank = False, False

        with open(p, 'r') as fp:
            # use big-endian
            gns = self._get_next_str(fp)

            def pgns():
                print gns()

            gh = self._get_short(fp)
            gs = self._get_single(fp)
            gl = self._get_long(fp)

            end_rec = int(gns())
            ignored_rid = gns()

            sample = gns()

            material = gns()
            investigator = gns()
            project = gns()
            locality = gns()
            rundate = gns()
            irradlabel = gns()
            fits = gns()
            comment = gns()
            runhour = gs()

            gof1, gof1 = gs(), gs()
            emv = [gs()]
            optemp = gs()

            ver = gs()
            print ver
            if ver > 4.96:
                emv.append(gs())

            if ver >= 4.6:
                history = gns()

            if ver >= 2:
                s1 = gs()
            else:
                s1 = 10 ^ 10
            scalefactor = s1, s1

            extract_device = ''
            if ver >= 4.46:
                extract_device = gns()

            extract_value = gs()
            fsp = extract_value
            if ver > 3.1:
                fsp = gs()  # final set power

            if extract_value == 0:
                if fsp > 0:
                    extract_value = fsp
                elif not (isref or isblank):
                    extract_value = float(comment)

            if ver > 4.34:
                totdur_heating = gl()
                todur_atsetpoint = gl()

            if ver > 2.32:
                gain = [gs()]

            if ver > 4.96:
                gain.append(gs())

            calc_with_ratio = bool(gh())
            system_number = 1
            if ver > 2.33:
                mol_ref_iso = gs()
                mol_ref_iso_special = mol_ref_iso < 0
                mol_ref_iso = abs(mol_ref_iso)

                system_number = gh()

            disc_source = 3
            if ver > 2.992:
                disc = gs()
                disc_err = gs()
                j = gs()
                jerr = gs()
                disc_source = 2

            resistor_values = [1, 1, 10 ^ 11]
            if ver > 4.02:
                resistor_values[2] = gs()
                resistor_values[0] = gs()
                if ver > 4.96:
                    resistor_values[1] = gs()
                if isref:
                    mol_ref_iso = gs()

            isogrp = 'Ar'
            if ver > 6.67 and ver < 7.245:
                isogrp = gns()
            elif ver >= 7.245:
                dum = gh()
            elif ver > 2.93 and ver < 6.67:
                grps = 'He,Ar,Ne,Kr,Xe'.split(',')

                # Mass Spec is 1-indexed
                idx = gh() - 1

                isogrp = grps[idx]

            niso = 5
            if ver > 2.96:
                niso = gh()

            nratio = 4
            if ver > 2.98:
                nratio = gh()

            if ver > 2.92:
                if ver < 3.1:
                    _, x = gs(), gs()

                dets = []
                for i in range(niso):
                    dt = gh()
                    if dt == 0:
                        dt = 1
                    dets.append(dt)
            else:
                dets = [1, ] * niso

            ndet = 1
            if ver >= 3.81:
                ndet = gh()
                if ndet > 1:
                    mx_det_type_n = 1
                    #                     det_conv_factor = []
                    for i in range(mx_det_type_n):
                        for j in range(i, mx_det_type_n, 1):
                            gs()

            elif ver >= 3.1:
                ndet = gh()
                if ndet > 1:
                    for i in range(ndet):
                        for j in range(ndet):
                            gs()

            refdetnum = 1
            if ver > 4.02:
                refdetnum = gh() or 1
            if ver > 2.994 and ver < 3.1:
                x = gs()

            signormfactor = 1
            if ver > 4:
                signormfactor = gs()

            ncyc = -1
            if ver > 2.994:
                ncyc = gh()

            if refdetnum == 16256:
                refdetnum = 1
                signnormfactor = 1
                ncyc = -1

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
                    numisokeys.append(gh())
                    demisokeys.append(gh())
            else:
                niso = 5
                nratio = 4
                isokeys = ['Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36',
                           'Ar40/Ar39',
                           'Ar38/Ar39',
                           'Ar37/Ar39',
                           'Ar36/Ar39',
                           'Bsln'
                ]
                numisokeys = [0, 2, 3, 4]
                demisokeys = [1, 1, 1, 1]
                if isref:
                    isokeys[5] = 'Ar40/Ar36'
                    isokeys[6] = 'Ar40/Ar38'
                    numisokeys = [1, 1, None, None]
                    demisokeys = [5, 3, None, None]

            ncnts = []
            isobsln = []
            for i in range(niso):
                ncnts.append(gs())
                v = self._load_signal(fp)
                isobsln.append(v)


    def _load_signal(self, fp):
        pass

#============= EOF =============================================
