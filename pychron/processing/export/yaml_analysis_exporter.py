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

# ============= enthought library imports =======================
import os

from traits.api import Instance

# ============= standard library imports ========================
# ============= local library imports  ==========================
from uncertainties import nominal_value, std_dev
import yaml
from pychron.processing.export.destinations import YamlDestination
from pychron.processing.export.exporter import Exporter


class YamlAnalysisExporter(Exporter):
    destination = Instance(YamlDestination, ())
    _ctx = None

    def clear(self):
        self._ctx = dict()

    def add(self, dbanalysis):
        if not self._ctx:
            self._ctx = dict()

        self._ctx[dbanalysis.record_id] = self._generate_analysis_dict(dbanalysis)

    def export(self, *args, **kw):
        p = self.destination.destination
        if os.path.isdir(os.path.dirname(p)):
            with open(p, 'w') as fp:
                fp.write(yaml.dump(self._ctx, default_flow_style=False))

    def _generate_analysis_dict(self, ai):
        """
            convert types to float,int,dict,list, etc
        """

        meta_attr = ('labnumber',
                     'aliquot',
                     'uuid',
                     'step', 'timestamp', 'tag',
                     'cleanup','duration','extract_value',
                     'sample', 'project', 'material', 'mass_spectrometer',
                     'comment',
                     'position',
                     'irradiation','irradiation_pos','irradiation_level',
                     ('age', float),
                     ('age_err', float),
                     ('age_err_wo_j', float),
                     ('age_err_wo_j_irrad', float),
                     ('ar37decayfactor', float),
                     ('ar39decayfactor',float))

        def func(args):
            cast=None
            if len(args)==2:
                k,cast=args
            else:
                k=args

            v=getattr(ai, k)
            if cast:
                v=cast(v)
            return k, v

        d = dict([func(args) for args in meta_attr])

        # d = {k: getattr(ai, k) for k in meta_attr}

        # for attr in ('age', 'age_err', 'age_err_wo_j', 'age_err_wo_j_irrad',
        #              'ar37decayfactor', 'ar39decayfactor'):
        #     d[attr] = float(ai, getattr(attr))

        self._generate_isotopes(ai, d)
        self._generate_irradiation(ai, d)
        d['constants'] = ai.arar_constants.to_dict()

        return d

    def _generate_irradiation(self, ai, d):
        d['production_ratios'] = dict(ai.production_ratios)

        ifc = ai.interference_corrections
        nifc = dict()
        for k, v in ifc.iteritems():
            nifc[k] = nominal_value(v)
            nifc['{}_err'.format(k)] = float(std_dev(v))

        d['interference_corrections'] = nifc
        d['chron_segments'] = [dict(zip(('power', 'duration', 'dt'), ci)) for ci in ai.chron_segments]
        d['irradiation_time'] = ai.irradiation_time

        d['j'] = float(ai.j.nominal_value)
        d['j_err'] = float(ai.j.std_dev)

    def _generate_isotopes(self, ai, d):
        def func(iso):
            return {'name': iso.name,
                    'detector': iso.detector,
                    'discrimination': float(iso.discrimination.nominal_value),
                    'discrimination_err': float(iso.discrimination.std_dev),
                    'ic_factor': float(iso.ic_factor.nominal_value),
                    'ic_factor_err': float(iso.ic_factor.std_dev),
                    'value': float(iso.value),
                    'error': float(iso.error),
                    'blank': float(iso.blank.value),
                    'blank_err': float(iso.blank.error),
                    'baseline': float(iso.baseline.value),
                    'baseline_err': float(iso.baseline.error),
                    'fit': iso.fit,
                    'filter_outliers': dict(iso.filter_outliers_dict),
                    'data': iso.pack()}

        d['isotopes'] = [func(ii) for ii in ai.isotopes.itervalues()]


#============= EOF =============================================



