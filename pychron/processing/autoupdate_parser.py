# ===============================================================================
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

#=============enthought library imports=======================
from traits.api import HasTraits, List, Dict
# from traitsui.api import View, Item

#============= standard library imports ========================
import csv
from pychron.loggable import Loggable
from pychron.pychron_constants import IRRADIATION_KEYS, DECAY_KEYS
#============= local library imports  ==========================
# from pychron.core.stats import calculate_mswd, calculate_weighted_mean
# from pychron.data_processing.argon_calculations import calculate_arar_age, find_plateaus


# def formatfloat(f, n=3):
#        if f > 1000:
#            n -= 1
#        return '{:0.{}f}'.format(f, n)

class Analysis(HasTraits):
    _params = Dict

    def __init__(self, p, *args, **kw):
        self._params = p
        super(Analysis, self).__init__(*args, **kw)

    def __getattr__(self, item):
        return self._params[item]


class Sample(HasTraits):
    analyses = List
    #    info = None
    def __init__(self, name):
        self.name = name
        self.analyses = []

    def add_analysis(self, a):
        self.analyses.append(a)


class AutoupdateParser(Loggable):
    samples = Dict

    def parse(self, p):
        with open(p, 'U') as f:
            reader = csv.reader(f, delimiter='\t')

            header = reader.next()

            sampleObj = None
            samples = dict()
            sample_group = 0
            #            sample_idx = header.index('Sample')
            for line in reader:
                get_value = lambda x, **kw: self._get_value(x, header, line, **kw)

                sample = get_value('Sample', cast=str)

                if not sample:
                    break

                if sampleObj is None or sampleObj.name != sample:
                    sampleObj = Sample(sample)
                    samples[sample] = sampleObj
                    #samples.append(sampleObj)
                    sample_group += 1

                params = dict()
                params['sample'] = sample
                params['material'] = get_value('Material', cast=str)
                params['sample_group'] = sample_group
                params['power'] = get_value('Pwr_Achieved')

                params['run_id'] = get_value('Run_ID', cast=str)
                params['age'] = get_value('Age')
                params['age_err'] = get_value('Age_Er')

                params['j'] = get_value('J')
                params['j_err'] = get_value('J_Er')

                try:
                    params['k_ca'] = 1 / float(get_value('Ca_Over_K'))
                except ZeroDivisionError:
                    params['k_ca'] = 0

                params['k_ca_err'] = get_value('Ca_Over_K_Er')

                params['rad40_percent'] = get_value('PctAr40Rad')
                params['rad40_percent_err'] = get_value('PctAr40Rad_Er')
                params['rad40'] = get_value('Ar40Rad_Over_Ar39')
                params['rad40_err'] = get_value('Ar40Rad_Over_Ar39_Er')

                params['Isoch_39_40'] = get_value('Isoch_39_Over_40')
                params['Isoch_36_40'] = get_value('Isoch_36_Over_40')
                params['Isoch_39_40err'] = get_value('Pct_i39_Over_40_Er')
                params['Isoch_36_40err'] = get_value('Pct_i36_Over_40_Er')

                fts = get_value('Fit_Type', cast=str)

                #mass spec measures 36 before 37
                for i, si in enumerate(('Ar40', 'Ar39', 'Ar38', 'Ar36', 'Ar37')):
                    params[si] = get_value('{}_'.format(si))
                    bs_only = '{}_BslnCorOnly'.format(si)
                    bs_only_err = '{}_Er_BslnCorOnly'.format(si)
                    params['{}Er'.format(si)] = get_value('{}_Er'.format(si))

                    params[bs_only] = get_value(bs_only)
                    params[bs_only_err] = get_value(bs_only_err)

                    btag = '{}_Bkgd'.format(si)
                    betag = '{}_BkgdEr'.format(si)
                    params[btag] = get_value(btag)
                    params[betag] = get_value(betag)

                    ctag = '{}_DecayCor'.format(si)
                    cetag = '{}_DecayCor'.format(si)
                    params[ctag] = get_value(ctag)
                    params[cetag] = get_value(cetag)
                    params['{}_fit'.format(si)] = fts[i]

                for attr, key in DECAY_KEYS:
                    params[attr] = float(get_value(key))

                for attr, key in IRRADIATION_KEYS:
                    params[attr] = get_value(key)
                    params['{}_err'.format(attr)] = get_value('{}_Er'.format(key))

                sampleObj.add_analysis(Analysis(params))

            self.samples = samples

    def _get_value(self, key, header, line, cast=float, default=None):
        try:
            v = line[header.index(key)]
            if cast:
                try:
                    v = cast(v)
                except ValueError:
                    v = 0
        except IndexError:
            v = default

        return v


if __name__ == '__main__':
    p = AutoupdateParser()
    pa = '/Users/ross/Antarctica/MinnaBluff/data/gm-06.csv'
    samples = p.parse(pa)

    print samples[0].get_isotopic_recombination_age()



#============= EOF =====================================
#    def finish(self):
#        self._calculate_cumulative39()
#        self.find_plateau_steps()
#
#    def _calculate_cumulative39(self):
#        s = sum([a.ar39_ for a in self.analyses])
#        pv = 0
#        for a in self.analyses:
#            v = a.ar39_ / s * 100
#            pv += v
#            a.ar39_percent = pv
#
#    def _get_summed_err(self, k):
#        return reduce(lambda x, y:(x ** 2 + y ** 2) ** 0.5, [getattr(a, k) for a in self.analyses])
#
#    def _calculate_isotopic_recombination(self):
#
#        ar40_sum = sum([a.ar40_ for a in self.analyses])
#        ar39_sum = sum([a.ar39_ for a in self.analyses])
#        ar38_sum = sum([a.ar38_ for a in self.analyses])
#        ar37_sum = sum([a.ar37_ for a in self.analyses])
#        ar36_sum = sum([a.ar36_ for a in self.analyses])
#
#        ar40er_sum = self._get_summed_err('ar40_er')
#        ar39er_sum = self._get_summed_err('ar39_er')
#        ar38er_sum = self._get_summed_err('ar38_er')
#        ar37er_sum = self._get_summed_err('ar37_er')
#        ar36er_sum = self._get_summed_err('ar36_er')
#
#        age, _err = calculate_arar_age((ar40_sum,
#                                      ar40er_sum,
#                                      ar39_sum,
#                                      ar39er_sum,
#                                      ar38_sum,
#                                      ar38er_sum,
#                                      ar37_sum,
#                                      ar37er_sum,
#                                      ar36_sum,
#                                      ar36er_sum),
#
#                                      (a.p36cl38cl,
#                                       a.k4039, a.k3839,
#                                       a.ca3637, a.ca3937, a.ca3837),
#
#                                      (a.k4039er, a.ca3637er, a.ca3937er),
#
#                                      a.a37decayfactor,
#                                      a.a39decayfactor,
#                                      a.j,
#                                      a.jer,
#                                      a.d,
#                                      a.der
#                                      )
# #        print '{:0.2f}'.format(2 * err.nominal_value), err.nominal_value / age.std_dev()
# #        print '{:0.2f}'.format(2 * err.nominal_value),
# #        print  '{:0.2f}'.format(4 * age.std_dev())
#
#        return age.nominal_value, 2 * age.std_dev() ** 0.5 / len(self.analyses)
#
#    def get_isotopic_recombination_age(self):
#        a, e = self._calculate_isotopic_recombination()
#
#
#        return a, e
#
#    def get_kca(self, plateau=False):
#        if plateau:
#            kcas = [a.k_over_ca for a in self.analyses if a.plateau_status]
#            kerr = [a.k_over_ca_er for a in self.analyses if a.plateau_status]
#            kca, err = calculate_weighted_mean(kcas, kerr)
#
#        else:
#            kcas = [a.k_over_ca for a in self.analyses]
#            err = 0
#            kca = 0
#        return kca, err
#
#    def get_plateau_age(self, nsigma=2):
#        x, errs = self._get_plateau_ages()
#        a, e = calculate_weighted_mean(x, errs)
#
#        mswd = self.get_mswd()
#        return a, nsigma * e * mswd ** 0.5
#
#    def get_plateau_percent39(self):
#        s = 0
#        tot = self.get_total39()
#        for a in self.analyses:
#            if a.plateau_status:
#                s += a.ar39_moles
#
#        return s / tot * 100
#
#    def get_total39(self, plateau=False):
#
#        if plateau:
#            s = [a.ar39_moles for a in self.analyses if a.plateau_status]
#        else:
#            s = [a.ar39_moles for a in self.analyses]
#
#        return sum(s)
#
#    def get_mswd(self, all_steps=False):
#        x, errs = self._get_plateau_ages(all_steps)
#        mw = calculate_mswd(x, errs)
#        return mw
#
#    def _get_plateau_ages(self, all_steps=False):
#        x = [a.age for a in self.analyses if a.plateau_status or all_steps]
#        errs = [a.age_er for a in self.analyses if a.plateau_status or all_steps]
#        return x, errs
#
#    def get_nsteps(self):
#        return len(self.analyses)
#
#    def get_plateau_steps(self):
#        ps = [a.suffix for a in self.analyses if a.plateau_status]
#        if ps:
#            return ps[0], ps[-1], len(ps)
#
#    def find_plateau_steps(self):
#        ages, errs = self._get_plateau_ages(all_steps=True)
#        signals = [a.ar39_ for a in self.analyses]
#        plat = find_plateaus(ages, errs, signals)
#        if plat[0] == plat[1]:
#            msg = 'no plateau found'
#
#        else:
#            tot = sum(signals)
#            per = sum(signals[plat[0]:plat[1] + 1]) / tot * 100
#            a = [chr(i) for i in range(65, 65 + 26)]
#            msg = '{}-{} {}'.format(a[plat[0]], a[plat[1]], '%0.1f' % per)
#
#            for a in self.analyses[plat[0]:plat[1] + 1]:
#                a.plateau_status = True
#                a.status = ''
#        print self.name, msg
# #        print ages[plat[0]:plat[1] + 1]

# class AutoupdateAnalysis(object):


#    plateau_status = False
#    status = 'X'
#    suffix = None
#    pwr_requested = None
#    ar40_over_ar39 = None
#    ar37_over_ar39 = None
#    ar36_over_ar39 = None
#    ar39_moles = None
#    k_over_ca = None
#    percent_40rad = None
#    age = None
#    age_er = None
#    ar39_percent = None
#
#
#    ar40_ = None
#    ar40_er = None
#    ar39_ = None
#    ar39_er = None
#    ar38_ = None
#    ar38_er = None
#    ar37_ = None
#    ar37_er = None
#    ar36_ = None
#    ar36_er = None
#
#    p36cl38cl = None
#    k4039 = None
#    k4039er = None
#    k3839 = None
#    ca3637 = None
#    ca3637er = None
#    ca3937 = None
#    ca3937er = None
#    ca3837 = None
#
#    a37decayfactor = None
#    a39decayfactor = None
#
#    d = None
#    der = None
#    def get_data(self):
#        d = []
#        for attr, fmt in [('status', None),
#                          ('suffix', None),
#                          ('pwr_requested', None),
#                          ('ar40_over_ar39', 3),
#                          ('ar37_over_ar39', 3),
#                          ('ar36_over_ar39', 3),
#                          ('ar39_moles', 3),
#                          ('k_over_ca', 2),
#                          ('percent_40rad', 1),
#                          ('ar39_percent', 1),
#                          ('age', 3),
#                          ('age_er', 3)
#                          ]:
#            v = getattr(self, attr)
#            if fmt:
#                v = formatfloat(v, n=fmt)
#            d.append(v)
#        return d

#                self.line = line
#                try:
#                    rid = self.get_value('Run_ID', cast=str)
#                    l_number, suffix = self._parse_rid(rid)
#
#
#                    if cursample is None or cursample.name != sample:
#                        if cursample is not None:
#                            samples.append(cursample)
#
# #                            cursample._calculate_cumulative39()
#                            cursample.finish()
#                        s = Sample(sample)
#                        weight, = self._parse_comment()
#
#                        j = self.get_value('J', cast=float)
#                        jer = self.get_value('J_Er', cast=float)
#                        jer_percent = formatfloat(jer / j * 100, n=2)
#                        s.info = dict(rid=rid,
#                                      sample=sample,
#                                      l_number=l_number,
#                                         irrad=self.get_value('Irrad', cast=str),
#                                         j=j,
#                                         jer=jer_percent,
#                                         d=self.get_value('Ar40_Disc'),
#                                         der=self.get_value('Ar40_DiscEr'),
#                                         material=self.get_value('Material', cast=str),
#                                         weight=weight
#                                         )
#                        cursample = s
#
#
# #                    status = self.get_value('Status', cast=str)
#                    a = AutoupdateAnalysis()
# #                    a.status = status
#                    a.suffix = suffix
#                    a.pwr_requested = self.get_value('Pwr_Requested', cast=str)
#                    a.ar40_over_ar39 = self.get_value('Ar40_Over_Ar39')
#                    a.ar37_over_ar39 = self.get_value('Ar37_Over_Ar39')
#                    a.ar36_over_ar39 = self.get_value('Ar36_Over_Ar39') * 1000
#                    a.ar39_moles = self.get_value('Ar39_Moles') * 1e15
#                    a.k_over_ca = self.get_value('Ca_Over_K') ** -1
#                    a.k_over_ca_er = self.get_value('Ca_Over_K_Er')
#                    a.percent_40rad = self.get_value('PctAr40Rad')
#                    a.age = self.get_value('Age')
#                    a.age_er = self.get_value('Age_Er')
#
# #                    a.plateau_status = False if 'x' in status.lower() else True
#
#                    a.ar39_ = self.get_value('Ar39_')
#
#                    a.ar40_ = self.get_value('Ar40_')
#                    a.ar40_er = self.get_value('Ar40_Er')
#                    a.ar39_ = self.get_value('Ar39_')
#                    a.ar39_er = self.get_value('Ar39_Er')
#                    a.ar38_ = self.get_value('Ar38_')
#                    a.ar38_er = self.get_value('Ar38_Er')
#                    a.ar37_ = self.get_value('Ar37_')
#                    a.ar37_er = self.get_value('Ar37_Er')
#                    a.ar36_ = self.get_value('Ar36_')
#                    a.ar36_er = self.get_value('Ar36_Er')
#                    a.p36cl38cl = self.get_value('P36Cl_Over_38Cl')
#                    a.k4039 = self.get_value('K_40_Over_39')
#                    a.k4039er = self.get_value('K_40_Over_39_Er')
#                    a.k3839 = self.get_value('K_38_Over_39')
#                    a.ca3637 = self.get_value('Ca_36_Over_37')
#                    a.ca3637er = self.get_value('Ca_36_Over_37_Er')
#                    a.ca3937 = self.get_value('Ca_39_Over_37')
#                    a.ca3937er = self.get_value('Ca_39_Over_37_Er')
#                    a.ca3837 = self.get_value('Ca_38_Over_37')
#
#                    a.a37decayfactor = self.get_value('37_Decay')
#                    a.a39decayfactor = self.get_value('39_Decay')
#                    a.j = self.get_value('J')
#                    a.jer = self.get_value('J_Er')
#                    a.d = self.get_value('Ar40_Disc')
#                    a.der = self.get_value('Ar40_DiscEr')
#
#                    cursample.analyses.append(a)
#
#                except IndexError, e:
#                    if not samples:
#                        samples.append(cursample)
#                        cursample._calculate_cumulative39()
#                    # finished reading analyses
#                    break
#
#            return samples
#    header = None
#    line = None
#    def get_value(self, line, idx, cast=float, default=''):
#        try:
#            v = line[self.header.index(key)]
#        except ValueError:
#            return default
# #        print len(line), self.header.index(key), v
#        return cast(v)
#
#    def _parse_rid(self, rid):
#        l_number = rid.split('-')[0] + '-'
#        suffix = ''
#        for s in rid.split('-')[1]:
#            try:
#                float(s)
#                l_number += str(s)
#            except:
#                suffix += s
#        return l_number, suffix

#    def _parse_comment(self):
#        comment = self.get_value('Comment', cast=str)
#
#        weight = comment.split(',')[1].split('mg')[0].strip()
#
#        return weight,
#    COLUMN_NAMES = ['Run_ID',
#                    'Sample',
#                    'System',
#                    'Run_Date',
#                    'Run_Hour',
#                    'Run_SecSince1904',
#                    'PrincipalInvestigator',
#                    'Material',
#                    'Hole #',
#                    'Project',
#                    'Locality',
#                    'File',
#                    'Version',
#                    'History',
#                    'Comment',
#                    'Fit_Type',
#                    'Signal Norm.',
#                    'Run Script',
#                    'Heating_Dev',
#                    'Pwr_Requested',
#                    'Pwr_Achieved',
#                    'Pwr_AchievedSD',
#                    'Pwr_AchievedMax',
#                    'OP_Temp',
#                    'Tot_Dur_Heating',
#                    'Dur_Heating_At_Req_Pwr',
#                    'Holes',
#                    'X_Y_Pos',
#                    'Laser Scan File',
#                    'Beam_Dia',
#                    'Ar40_',
#                    'Ar40_Er',
#                    'Ar39_',
#                    'Ar39_Er',
#                    'Ar38_',
#                    'Ar38_Er',
#                    'Ar36_',
#                    'Ar36_Er',
#                    'Ar37_',
#                    'Ar37_Er',
#                    'Ar35_',
#                    'Ar35_Er',
#                    'Ar40_BslnCorOnly',
#                    'Ar40_Er_BslnCorOnly',
#                    'Ar39_BslnCorOnly',
#                    'Ar39_Er_BslnCorOnly',
#                    'Ar38_BslnCorOnly',
#                    'Ar38_Er_BslnCorOnly',
#                    'Ar36_BslnCorOnly',
#                    'Ar36_Er_BslnCorOnly',
#                    'Ar37_BslnCorOnly',
#                    'Ar37_Er_BslnCorOnly',
#                    'Ar35_BslnCorOnly',
#                    'Ar35_Er_BslnCorOnly',
#                    'Ar40_Disc',
#                    'Ar40_DiscEr',
#                    'Ar39_Disc',
#                    'Ar39_DiscEr',
#                    'Ar38_Disc',
#                    'Ar38_DiscEr',
#                    'Ar36_Disc',
#                    'Ar36_DiscEr',
#                    'Ar37_Disc',
#                    'Ar37_DiscEr',
#                    'Ar35_Disc',
#                    'Ar35_DiscEr',
#                    'Ar40_ICFactor',
#                    'Ar40_ICFactorEr',
#                    'Ar39_ICFactor',
#                    'Ar39_ICFactorEr',
#                    'Ar38_ICFactor',
#                    'Ar38_ICFactorEr',
#                    'Ar36_ICFactor',
#                    'Ar36_ICFactorEr',
#                    'Ar37_ICFactor',
#                    'Ar37_ICFactorEr',
#                    'Ar35_ICFactor',
#                    'Ar35_ICFactorEr',
#                    'Ar40_Bkgd',
#                    'Ar40_BkgdEr',
#                    'Ar39_Bkgd',
#                    'Ar39_BkgdEr',
#                    'Ar38_Bkgd',
#                    'Ar38_BkgdEr',
#                    'Ar36_Bkgd',
#                    'Ar36_BkgdEr',
#                    'Ar37_Bkgd',
#                    'Ar37_BkgdEr',
#                    'Ar35_Bkgd',
#                    'Ar35_BkgdEr',
#                    'Ar36_Over_Ar39',
#                    'Ar36_Over_Ar39_Er',
#                    'PctAr36Ca',
#                    'Ar37_Over_Ar39',
#                    'Ar37_Over_Ar39_Er',
#                    'Ca_Over_K',
#                    'Ca_Over_K_Er',
#                    'Cl_Over_K',
#                    'Cl_Over_K_Er',
#                    'Ar38_Over_Ar39',
#                    'Ar38_Over_Ar39_Er',
#                    'Ar40_Over_Ar39',
#                    'Ar40_Over_Ar39_Er',
#                    'Ar40Rad_Over_Ar39',
#                    'Ar40Rad_Over_Ar39_Er',
#                    'PctAr40Rad',
#                    'PctAr40Rad_Er',
#                    'Age',
#                    'Age_Er',
#                    'Age_Er_with_J_er',
#                    'Age_Monte_Carlo',
#                    'Age_Er_with_external_error',
#                    'Ar39_Moles',
#                    'Ar40_Moles',
#                    'Fract_Deliv_To_MS',
#                    'Irrad',
#                    'J',
#                    'J_Er',
#                    '37_Decay',
#                    '39_Decay',
#                    'Ca_39_Over_37',
#                    'Ca_39_Over_37_Er',
#                    'Ca_38_Over_37',
#                    'Ca_38_Over_37_Er',
#                    'Ca_36_Over_37',
#                    'Ca_36_Over_37_Er',
#                    'K_38_Over_39',
#                    'K_38_Over_39_Er',
#                    'K_40_Over_39',
#                    'K_40_Over_39_Er',
#                    'K_37_Over_39',
#                    'K_37_Over_39_Er',
#                    'P36Cl_Over_38Cl',
#                    'P36Cl_Over_38Cl_Er',
#                    'Ca_Over_K_Multiplier',
#                    'Ca_Over_K_Multiplier_Er',
#                    'Ar40_DecayCor',
#                    'Ar40_DecayCorEr',
#                    'Ar39_DecayCor',
#                    'Ar39_DecayCorEr',
#                    'Ar38_DecayCor',
#                    'Ar38_DecayCorEr',
#                    'Ar36_DecayCor',
#                    'Ar36_DecayCorEr',
#                    'Ar37_DecayCor',
#                    'Ar37_DecayCorEr',
#                    'Ar35_DecayCor',
#                    'Ar35_DecayCorEr',
#                    'Isoch_36_Over_40',
#                    'Pct_i36_Over_40_Er',
#                    'Isoch_39_Over_40',
#                    'Pct_i39_Over_40_Er',
#                    'Pct_i39_Over_36_Er',
#                    'Correl_40_Over_39',
#                    'Correl_36_Over_39',
#                    'Lambda_40K_epsilon',
#                    'Lambda_40K_epsilon_Er',
#                    'Lambda_40K_Beta',
#                    'Lambda_40K_Beta_Er',
#                    'Lambda_Ar37',
#                    'Lambda_Ar37_Er',
#                    'Lambda_Ar39',
#                    'Lambda_Ar39_Er',
#                    'Lambda_36Cl',
#                    'Lambda_36Cl_Er',
#                    '40K_abundance',
#                    '40K_abundance_Er',
#                    'Air_40_Over_36',
#                    'Air_40_Over_36_Er',
#                    'Air_40_Over_38',
#                    'Air_40_Over_38_Er',
#                    'K38_Over_39',
#                    'Cl38_Over_39',
#                    'Cold Finger_Ave',
#                    'Furnace Water_Ave',
#                    'Lab Humid_Ave',
#                    'Lab Temp_Ave',
#                    'Pneumatics_Ave'
#                    ]
