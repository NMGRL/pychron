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
from lxml import etree

from pychron.loggable import Loggable

NSMAP = {None: 'http://matisse.kgs.ku.edu/arar/schema',
         'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}


class GeochronService(Loggable):
    def assemble_xml(self, analysis_group):
        root = etree.Element('ArArModel', nsmap=NSMAP)
        doc = etree.ElementTree(root)

        self._add_sample(root, analysis_group)

        with open('/Users/ross/Desktop/foo.xml', 'w') as wfile:
            wfile.write(etree.tostring(doc, pretty_print=True))

    def _add_sample(self, root, analysis_group):
        sample_elem = etree.SubElement(root, 'Sample')

        sample = analysis_group.sample
        for attr in ('sampleID', 'igsn', 'longitude', 'latitude', 'analystName'):
            sample_elem.attrib[attr] = getattr(sample, attr)

        self._add_preferred_age(sample_elem, analysis_group)
        self._add_interpreted_ages()
        self._add_parameters()

    def _add_preferred_age(self, sample_elem, analysis_group):

        preferred_age = analysis_group.preferred_age

        preferred_age_elem = etree.SubElement(sample_elem, 'PreferredAge')
        for attr in ('preferredAge', 'preferredAgeSigma', 'preferredAgeSigmaInternal',
                     'preferredAgeSigmaExternal', 'preferredAgeType', 'preferredAgeClassification',
                     'preferredAgeReference', 'preferredAgeDescription'):
            preferred_age_elem.attrib[attr] = getattr(preferred_age, attr)

        experiments_included_elem = etree.SubElement(preferred_age_elem, 'ExperimentsIncluded')
        for analysis in analysis_group.analyses:
            experiments_elem = etree.SubElement(experiments_included_elem, 'Experiment')
            experiments_elem.attrib['experimentIdentifier'] = analysis.runid

    def _add_interpreted_ages(self):
        pass

    def _add_parameters(self, sample_elem):
        param_elem = etree.SubElement(sample_elem, 'Parameters')
        experiment_elem = etree.SubElement(param_elem, 'Experiment')
        self._add_irradiation(experiment_elem, irrad)

    def _add_irradiation(self, experiment_elem, irrad):
        irradiation_elem = etree.SubElement(experiment_elem, 'Irradiation')
        attrs = (('irradiationName', '', False),
                 ('irradiationReactorName', '', True),
                 ('irradiationTotalDuration', '', False),
                 ('irradiationEndDateTime', '', False),
                 ('irradiationPower', '', False),
                 ('irradiationSegmentList', '', False),
                 ('irradiationDescription', '', False))

        for attr, iattr, required in attrs:
            val = self._get_attr(irrad, attr, iattr, required)
            if val is not None:
                irradiation_elem.attrib[attr] = val

        attrs = (('correction40Ar36ArAtmospheric', '', True),
                 ('correction40Ar36ArAtmosphericSigma', '', True),
                 ('correction40Ar36ArCosmogenic', '', False),
                 ('correction40Ar36ArCosmogenicSigma', '', False),
                 ('correction38Ar36ArAtmospheric', '', True),
                 ('correction38Ar36ArAtmosphericSigma', '', True),
                 ('correction38Ar36ArCosmogenic', '', False),
                 ('correction38Ar36ArCosmogenicSigma', '', False),
                 ('correction39Ar37ArCalcium', 'Ca3937', True),
                 ('correction39Ar37ArCalciumSigma', 'Ca3937_err', True),
                 ('correction38Ar37ArCalcium', 'Ca3837', True),
                 ('correction38Ar37ArCalciumSigma', 'Ca3837_err', True),
                 ('correction36Ar37ArCalcium', 'Ca3637', True),
                 ('correction36Ar37ArCalciumSigma', 'Ca3637_err', True),
                 ('correction40Ar39ArPotassium', 'K4039', True),
                 ('correction40Ar39ArPotassiumSigma', 'K4039_err', True),
                 ('correction38Ar39ArPotassium', 'K3839', True),
                 ('correction38Ar39ArPotassiumSigma', 'K3839_err', True),
                 ('chlorineProductionRatio36Ar38Ar', 'Cl3638', False),
                 ('chlorineProductionRatio36Ar38ArSigma', 'Cl3638_err', False),
                 ('correctionKCa', 'K_Ca', False),
                 ('correctionKCaSigma', 'K_Ca_err', False),
                 ('correctionKCl', 'Cl_K', False),
                 ('correctionKClSigma', 'Cl_K_err', False),
                 ('correctionCaCl', 'Ca_Cl', False),
                 ('correctionCaClSigma', 'Ca_Cl_err', False))

        production = irrad.production
        for attr, iattr, required in attrs:
            val = self._get_attr(production, attr, iattr, required)
            if val is not None:
                irradiation_elem.attrib[attr] = val

        segments = irrad.chronology
        for i, seg in enumerate(segments):
            seg_elem = etree.SubElement(irradiation_elem)
            seg_elem.attrib['segmentNumber'] = i
            seg_elem.attrib['segmentDuration'] = i
            seg_elem.attrib['segmentDate'] = i
            seg_elem.attrib['segmentEndTime'] = i
            seg_elem.attrib['segmentPowerSetting'] = i

    def _get_attr(self, obj, attr, iattr, required):
        val = None
        try:
            val = getattr(obj, iattr)
        except AttributeError:
            if required:
                self.warning_dialog('Required attribute "{}" not supplied. Contact developer'.format(attr))

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


    ag = AnalysisGroup()

    g = GeochronService()
    g.assemble_xml(ag)
# ============= EOF =============================================
