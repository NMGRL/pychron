#===============================================================================
# Copyright 2012 Jake Ross
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
from numpy import std, mean, where, delete
from traits.api import CStr, Str, CInt, Float, \
    TraitError, Property, Any, Either, Dict, Bool, List
from uncertainties import ufloat

from pychron.loggable import Loggable






#============= standard library imports ========================
#============= local library imports  ==========================


class ExportSpec(Loggable):
    runid = CStr
    aliquot = Either(CInt, Str)
    step = Str
    irradpos = CStr

    isotopes=Dict

    mass_spectrometer = Str
    extract_device = Str
    tray = Str
    position = Property(depends_on='_position')
    _position = Any

    timestamp = Float
    power_requested = Float(0)
    power_achieved = Float(0)
    duration = Float(0)
    duration_at_request = Float(0)
    first_stage_delay = CInt(0)
    second_stage_delay = CInt(0)
    runscript_name = Str
    runscript_text = Str
    comment = Str

    # data_path = Str
    # data_manager = Instance(H5DataManager, ())
    update_rundatetime = Bool
    is_peak_hop = Bool
    peak_hop_detector = 'CDD'
    ic_factor_v = Float
    ic_factor_e = Float

    pr_dict = Dict
    chron_dosages = List
    interference_corrections = Dict
    production_name = Str
    j = Any

    def load_record(self, record):
        attrs = [('labnumber', 'labnumber'),
                 ('aliquot', 'aliquot'),
                 ('step', 'step'),
                 ('irradpos', 'labnumber'),
                 ('timestamp', 'timestamp'),
                 ('extract_device', 'extract_device'), ('tray', 'tray'),
                 ('position', 'position'), ('power_requested', 'extract_value'),
                 ('power_achieved', 'extract_value'), ('duration', 'duration'),
                 ('duration_at_request', 'duration'), ('first_stage_delay', 'duration'),
                 ('second_stage_delay', 'cleanup'),
                 ('comment', 'comment'),
                 ('irradiation', 'irradiation'),
                 ('irradiation_position', 'irradiation_pos'),
                 ('level', 'irradiation_level'),
        ]

        if hasattr(record, 'spec'):
            spec = record.spec
        else:
            spec = record

        for exp_attr, run_attr in attrs:
            if hasattr(spec, run_attr):
                try:
                    setattr(self, exp_attr, getattr(spec, run_attr))
                except TraitError, e:
                    self.debug(e)

        # if hasattr(record, 'cdd_ic_factor'):
        #     ic = record.cdd_ic_factor
        #     if ic is None:
        #         self.debug('Using default CDD IC factor 1.0')
        #         ic = ufloat(1, 1.0e-20)
        #
        #     self.ic_factor_v = float(ic.nominal_value)
        #     self.ic_factor_e = float(ic.std_dev)
        # else:
        #     self.debug('{} has no ic_factor attribute'.format(record, ))

        for a in ('chron_dosages',
                  'production_ratios',
                  'interference_corrections',
                  'production_name', 'j'):
            if hasattr(record, a):
                setattr(self, a, getattr(record, a))

    # def open_file(self):
    #     return self.data_manager.open_file(self.data_path)

    def iter_isotopes(self):
        return ((iso.name, iso.detector) for iso in self.isotopes.itervalues())
        # def _iter():
        #     dm = self.data_manager
        #     hfile = dm._frame
        #     root = dm._frame.root
        #     signal = root.signal
        #     for isogroup in hfile.listNodes(signal):
        #         for dettable in hfile.listNodes(isogroup):
        #             iso = isogroup._v_name
        #             det = dettable.name
        #             self.debug('iter_isotopes yield: {} {}'.format(iso, det))
        #             yield iso, det
        #
        # return _iter()

    def get_ncounts(self, iso):
        try:
            n = self.isotopes[iso].n
        except KeyError:
            n = 1
        return n

    def get_baseline_position(self, iso):
        return 39.5

    def get_blank_uvalue(self, iso):
        try:
            b = self.isotopes[iso].blank.get_baseline_corrected_value()
        except KeyError:
            self.debug('no blank for {} {}'.format(iso, self.isotopes.keys()))
            b = ufloat(0, 0)

        return b

    def get_signal_uvalue(self, iso, det):
        try:
            ps=self.isotopes[iso].uvalue
            # ps = self.signal_intercepts['{}signal'.format(iso)]
        except KeyError, e:
            self.debug('no key {} {}'.format(iso,
                                             self.isotopes.keys()))
            ps = ufloat(0, 0)

        return ps

    def get_signal_fit(self, iso):
        try:
            f=self.isotopes[iso].get_fit(-1)
        except KeyError:
            f = 'linear'
        return f

    def get_baseline_fit(self, det):
        return 'average_SEM'

    def get_baseline_data(self, iso, det, **kw):
        """
            det is the original detector not the mass spec fooling detector
        """
        self.debug('get baseline data {} {}'.format(iso, det))
        # if self.is_peak_hop and det == self.peak_hop_detector:
        #     iso = None

        return self._get_data('baseline', iso, det)

    def get_signal_data(self, iso, det, **kw):
        self.debug('get signal data {} {}'.format(iso, det))
        return self._get_data('signal', iso, det, **kw)

    def get_filtered_baseline_uvalue(self, iso, nsigma=2, niter=1):
        m,s=0,0
        n_filtered_pts = 0
        if iso in self.isotopes:
            iso=self.isotopes[iso]
            xs,ys=iso.baseline.xs, iso.baseline.ys
            for i in range(niter):
                m,s=mean(ys), std(ys)
                res=abs(ys-m)

                outliers=where(res > (s * nsigma))[0]
                ys=delete(ys, outliers)
                n_filtered_pts += len(outliers)

            m, s = mean(ys), std(ys)

        return ufloat(m, s), len(ys)

    def get_baseline_uvalue(self, iso):
        try:
            v=self.isotopes[iso].baseline.uvalue
        except KeyError:
            v=ufloat(0,0)
        return v

    # def get_baseline_uvalue(self, det):
        # vb = []
        #
        # dm = self.data_manager
        # hfile = dm._frame
        # root = dm._frame.root
        # v, e = 0, 0
        # if hasattr(root, 'baseline'):
        #     baseline = root.baseline
        #     for isogroup in hfile.listNodes(baseline):
        #         for dettable in hfile.listNodes(isogroup):
        #             if dettable.name == det:
        #                 vb = [r['value'] for r in dettable.iterrows()]
        #                 break
        #
        #     vb = array(vb)
        #     v = vb.mean()
        #     e = vb.std()
        #
        # return ufloat(v, e)

    # def _get_baseline_detector(self, iso, det):
    #     if self.is_peak_hop:
    #         det = self.peak_hop_detector
    #         msg = 'is_peak_hop using peak_hop_det baseline {} for {}'.format(det, iso)
    #         self.debug(msg)
    #     return det

    def _get_data(self, group, iso, det, verbose=True):
        try:
            iso = self.isotopes[iso]
            if group!='signal':
                iso=getattr(iso, group)
            t, v = iso.xs, iso.ys

        except KeyError:
            t, v = [0, ], [0, ]

        self.debug('Get data {} {} len t={}'.format(group, iso, len(t)))
        return t, v
        #
        # dm = self.data_manager
        # hfile = dm._frame
        # root = hfile.root
        #
        # try:
        #     group = getattr(root, group)
        #     if iso is None:
        #         tab = next((di for ii in hfile.listNodes(group)
        #                     for di in hfile.listNodes(ii)
        #                     if di.name == det))
        #     else:
        #         isog = getattr(group, iso)
        #         tab = getattr(isog, det)
        #
        #     data = [(row['time'], row['value'])
        #             for row in tab.iterrows()]
        #     t, v = zip(*data)
        # except (NoSuchNodeError, AttributeError, StopIteration):
        #     import traceback
        #
        #     if verbose:
        #         self.debug(traceback.format_exc())
        #
        #     t, v = [0, ], [0, ]
        #
        # return t, v

    #@property
    #def runid(self):
    #    return make_rid(self.labnumber, self.aliquot, self.step)

    def _set_position(self, pos):
        if ',' in pos:
            self._position = list(map(int, pos.split(',')))
        else:
            self._position = pos

    def _get_position(self):
        return self._position

        #============= EOF =============================================


def assemble_script_blob(scripts, kinds=None):
    """
        make one blob of all the script text

        return csv-list of names, blob
    """
    if kinds is None:
        kinds = ['extraction', 'measurement', 'post_equilibration', 'post_measurement']

    ts = []
    for (name, blob), kind in zip(scripts, kinds):
        ts.append('#' + '=' * 79)
        ts.append('# {} SCRIPT {}'.format(kind.replace('_', ' ').upper(), name))
        ts.append('#' + '=' * 79)
        if blob:
            ts.append(blob)

    return 'Pychron Script', '\n'.join(ts)