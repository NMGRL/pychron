# ===============================================================================
# Copyright 2016 ross
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= standard library imports ========================
# ============= local library imports  ==========================
import os

from lxml import etree
from uncertainties import nominal_value, std_dev

from pychron.geochron.definitions import NSMAP, EXPERIMENT_ATTRS, PRODUCTION_ATTRS, \
    MEASUREMENT_ATTRS, SAMPLE_ATTRS
from pychron.loggable import Loggable
from pychron.paths import paths


class GeochronService(Loggable):
    def load_schema(self):
        p = os.path.join(paths.data_dir, 'geochron_arar_schema.xsd')
        self._schema = etree.XMLSchema(file=p)

        print self._schema

    def assemble_xml(self, analysis_group):
        root = etree.Element('ArArModel', nsmap=NSMAP)
        doc = etree.ElementTree(root)

        self._add_sample(root, analysis_group)
        return etree.tostring(doc, pretty_print=True)

    def _add_sample(self, root, analysis_group):
        sample_elem = etree.SubElement(root, 'Sample')

        analysis = analysis_group.analyses[0]
        for attr, iattr, required in SAMPLE_ATTRS:
            val = self._get_value(analysis, attr, iattr, required)
            if val is not None:
                sample_elem.attrib[attr] = val

        self._add_preferred_age(sample_elem, analysis_group)
        self._add_interpreted_ages()
        self._add_parameters(sample_elem, analysis_group)

    def _add_preferred_age(self, sample_elem, analysis_group):

        # preferred_age = analysis_group.preferred_age

        preferred_age_elem = etree.SubElement(sample_elem, 'PreferredAge')

        # for attr, iattr, required in PREFERRED_AGE_ATTRS:
        #     val = self._get_value(preferred_age, attr, iattr, required)
        #     if val is not None:
        #         preferred_age_elem.attrib[attr] = val

        experiments_included_elem = etree.SubElement(preferred_age_elem, 'ExperimentsIncluded')
        for analysis in analysis_group.analyses:
            experiments_elem = etree.SubElement(experiments_included_elem, 'Experiment')
            experiments_elem.attrib['experimentIdentifier'] = analysis.record_id

    def _add_interpreted_ages(self):
        pass

    def _add_parameters(self, sample_elem, analysis_group):
        param_elem = etree.SubElement(sample_elem, 'Parameters')

        ref = analysis_group.analyses[0]

        param_elem.attrib['standardName'] = ref.standard_name
        param_elem.attrib['standardAge'] = str(nominal_value(ref.standard_age))
        param_elem.attrib['standardAgeSigma'] = str(std_dev(ref.standard_age))
        param_elem.attrib['standardMaterial'] = ref.standard_material

        param_elem.attrib['decayConstant40ArTotal'] = str(nominal_value(ref.arar_constants.lambda_k))
        param_elem.attrib['decayConstant40ArTotalSigma'] = str(std_dev(ref.arar_constants.lambda_k))
        param_elem.attrib['jValue'] = str(nominal_value(ref.j))
        param_elem.attrib['jValueSigma'] = str(std_dev(ref.j))

        # for attr, iattr, required in PARAMETER_ATTRS:
        #     if
        #
        #
        #     val = self._get_value(analysis_group, attr, iattr, required)
        #     if val is not None:
        #         param_elem.attrib[attr] = val

        self._add_experiment(param_elem, analysis_group)

    def _add_experiment(self, param_elem, analysis_group):
        experiment_elem = etree.SubElement(param_elem, 'Experiment')

        ref = analysis_group.analyses[0]
        for attr, iattr, required in EXPERIMENT_ATTRS:
            val = self._get_value(ref, attr, iattr, required)
            if val is not None:
                experiment_elem.attrib[attr] = val

        for ai in analysis_group.analyses:
            self._add_irradiation(experiment_elem, ai)
            self._add_measurement(experiment_elem, ai)

    def _add_measurement(self, experiment_elem, analysis):
        measurement_elem = etree.SubElement(experiment_elem, 'Measurement')
        for attr, iattr, required in MEASUREMENT_ATTRS:
            val = self._get_value(analysis, attr, iattr, required)
            if val is not None:
                measurement_elem.attrib[attr] = val

        measurement_elem.attrib['interceptUnit'] = 'fA'
        measurement_elem.attrib['blankUnit'] = 'fA'
        for k in ('36', '37', '38', '39', '40'):
            iso = analysis.get_isotope('Ar{}'.format(k))
            v = iso.get_baseline_corrected_value()
            tag = 'intercept{}Ar'.format(k)
            measurement_elem.attrib[tag] = str(nominal_value(v))
            measurement_elem.attrib['{}Sigma'.format(tag)] = str(std_dev(v))
            measurement_elem.attrib['{}RegressionType'.format(tag)] = iso.fit

            v = iso.blank.uvalue
            tag = 'blank{}Ar'.format(k)
            measurement_elem.attrib[tag] = str(nominal_value(v))
            measurement_elem.attrib['{}Sigma'.format(tag)] = str(std_dev(v))

    def _add_irradiation(self, experiment_elem, analysis):
        irradiation_elem = etree.SubElement(experiment_elem, 'Irradiation')

        irradiation_elem.attrib['irradiationName'] = analysis.irradiation
        irradiation_elem.attrib['irradiationReactorName'] = analysis.production_obj.reactor

        production = analysis.production_obj
        constants = analysis.arar_constants
        for attr, iattr, required in PRODUCTION_ATTRS:
            if attr in ('correction40Ar36ArAtmospheric', 'correction40Ar36ArAtmosphericSigma',
                        'correction38Ar36ArAtmospheric', 'correction38Ar36ArAtmosphericSigma'):
                val = self._get_value(constants, attr, iattr, required)
            else:
                val = self._get_value(production, attr, iattr, required)

            if val is not None:
                irradiation_elem.attrib[attr] = val

        segments = analysis.chron_dosages
        for i, (pwr, start, end) in enumerate(segments):
            seg_elem = etree.SubElement(irradiation_elem, 'Segment')
            seg_elem.attrib['segmentNumber'] = str(i)
            seg_elem.attrib['segmentDuration'] = str((end - start).total_seconds() / 3600.)
            seg_elem.attrib['segmentDate'] = start.strftime('%Y:%m:%d')
            seg_elem.attrib['segmentEndTime'] = end.strftime('%H:%M')
            seg_elem.attrib['segmentPowerSetting'] = str(pwr)

    def _get_value(self, obj, attr, iattr, required):
        if not iattr:
            iattr = attr

        val = None
        try:
            val = str(getattr(obj, iattr))
        except AttributeError:
            if required:
                self.warning_dialog('Required attribute "{}" not supplied. Contact developer'.format(attr))
        self.debug('get value {:>15s}, {:>15s}={:>15s}'.format(attr, iattr, val))
        return val


if __name__ == '__main__':
    class PreferredAgeSpec:
        preferredAge = '64.05'
        preferredAgeSigma = '0.116406054716396'
        preferredAgeSigmaInternal = '0.23'
        preferredAgeSigmaExternal = '23.23'
        preferredAgeType = 'Age Plateau'
        preferredAgeClassification = 'Eruption Age'
        preferredAgeReference = 'Koppers, A.A.P., Yamazaki, T., Geldmacher, J., Gee, J.S., Pressling, N., Hoshi, H. and the IODP Expedition 330 Science Party (2012). Limited latitudinal mantle plume motion for the Louisville hotspot. Nature Geoscience: doi: 10.1038/NGEO1638.'
        preferredAgeDescription = 'Classical groundmass age spectrum with high apparent ages for the low temperature steps due to remaining alteration in this submarine basaltic material and 39Ar recoil effects. The middle section reflects the primary argon being released from the groundmass giving the eruption age of the sample, mostly free of alteration and recoil effects. The high temparature steps give lower apparent ages due to recoil effect on 37Ar when outgassing the Calcium-rich clinopyroxene and plagioclase groundmass phases. The fact that the plateau age is concordant with both isochron ages and the total fusion age provides confidence in this interpretation.'


    class SampleSpec:
        sampleID = '330-U1376A-23R-3 33-37 cm'
        igsn = 'MY_IGSN_HERE'
        longitude = '-171.8806667'
        latitude = '-32.2165'
        analystName = 'Anthony Koppers'


    class AnalysisSpec:
        runid = '12313-01A'


    class AnalysisGroup:
        sample = SampleSpec()
        analyses = [AnalysisSpec()]
        preferred_age = PreferredAgeSpec()


    paths.build('_dev')
    ag = AnalysisGroup()

    g = GeochronService()
    # g.load_schema()
    g.assemble_xml(ag)
# ============= EOF =============================================
