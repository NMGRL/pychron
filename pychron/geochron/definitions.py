# ===============================================================================
# Copyright 2016 ross
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

# ============= standard library imports ========================
# ============= local library imports  ==========================
NSMAP = {None: 'http://matisse.kgs.ku.edu/arar/schema',
         'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}

"""
Definitions are lists of 3-tuples

   (xml_attribute_name, object_attribute_name, required)

    if object_attribute_name is not defined then xml_attribute_name is used instead

    True ==> attribute is required
"""
SAMPLE_ATTRS = (('sampleID', 'sample', True),
                ('sampleOtherName', '', False),
                ('igsn', '', True),
                ('longitude', '', True),
                ('latitude', '', True),
                ('analystName', '', True),
                ('imageURL', '', False))

EXPERIMENT_ATTRS = (('experimentIdentifier', '', True),
                    ('experimentType', 'experiment_type', True),
                    ('sampleMaterial', 'material', True),
                    ('sampleMaterialType', 'material', True),
                    ('mineralName', '', False),
                    ('sampleGrainSizeFraction', '', False),
                    ('sampleTreatment', '', False),
                    ('sampleWeight', '', False),
                    ('igsn', '', False),
                    ('projectName', 'project', False),
                    ('extractionMethod', 'extract_device', False),
                    ('massSpectrometer', 'mass_spectrometer', False),
                    ('laboratory', '', True),
                    ('laboratoryReference', '', False),
                    ('instrumentName', 'instrument_name', False),
                    ('acquisitionSoftware', 'acquisition_software', False),
                    ('dataReductionSoftware', 'data_reduction_software', False),
                    ('sampleDescription', '', False),
                    ('experimentDescription', '', False))

IRRADIATION_ATTRS = (('irradiationName', 'irradiation', False),
                     ('irradiationReactorName', '', True),
                     ('irradiationTotalDuration', '', False),
                     ('irradiationEndDateTime', '', False),
                     ('irradiationPower', '', False),
                     ('irradiationSegmentList', '', False),
                     ('irradiationDescription', '', False))

PRODUCTION_ATTRS = (('correction40Ar36ArAtmospheric', 'atm4036_v', True),
                    ('correction40Ar36ArAtmosphericSigma', 'atm4036_e', True),
                    ('correction40Ar36ArCosmogenic', '', False),
                    ('correction40Ar36ArCosmogenicSigma', '', False),
                    ('correction38Ar36ArAtmospheric', 'atm3836_v', True),
                    ('correction38Ar36ArAtmosphericSigma', 'atm3836_e', True),
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
                    ('correctionKCa', 'k_ca', False),
                    ('correctionKCaSigma', 'k_ca_err', False),
                    ('correctionKCl', 'k_cl', False),
                    ('correctionKClSigma', 'k_cl_err', False),
                    ('correctionCaCl', '', False),
                    ('correctionCaClSigma', '', False))

PREFERRED_AGE_ATTRS = (('preferredAge', '', True),
                       ('preferredAgeSigma', '', True),
                       ('preferredAgeSigmaInternal', '', True),
                       ('preferredAgeSigmaExternal', '', False),
                       ('preferredAgeType', '', True),
                       ('preferredAgeClassification', '', True),
                       ('preferredAgeReference', '', True),
                       ('preferredAgeDescription', '', False))

PARAMETER_ATTRS = (('standardName', '', True),
                   ('standardReference', '', False),
                   ('standardMaterial', '', True),
                   ('standardBatch', '', False),
                   ('standardAge', '', True),
                   ('standardAgeSigma', '', False),
                   ('standardAge40ArAbundance', '', False),
                   ('standardAge40ArAbundanceSigma', '', False),
                   ('standardAgeKAbundance', '', False),
                   ('standardAgeKAbundanceSigma', '', False),
                   ('standardAge40Ar40KRatio', '', False),
                   ('standardAge40Ar40KRatioSigma', '', False),
                   ('decayConstant40ArTotal', '', True),
                   ('decayConstant40ArTotalSigma', '', True),
                   ('decayConstant40ArBeta', '', False),
                   ('decayConstant40ArBetaSigma', '', False),
                   ('decayConstant40ArElectron', '', False),
                   ('decayConstant40ArElectronSigma', '', False),
                   ('activity40ArBeta', '', False),
                   ('activity40ArBetaSigma', '', False),
                   ('activity40ArElectron', '', False),
                   ('activity40ArElectronSigma', '', False),
                   ('avogadroNumber', '', False),
                   ('solarYear', '', False),
                   ('atomicWeightK', '', False),
                   ('atomicWeightKSigma', '', False),
                   ('abundanceRatio40KK', '', False),
                   ('abundanceRatio40KKSigma', '', False),
                   ('jValue', 'j', True),
                   ('jValueSigma', 'jerr', True),
                   ('parametersDescription', '', False))

MEASUREMENT_ATTRS = (('measurementNumber', 'record_id', True),
                     ('measurementDateTime', 'timestamp', True),
                     ('temperature', 'extract_value', True),
                     ('temperatureSigma', '', False),
                     ('temperatureUnit', 'extract_units', True),
                     ('heatingDuration', 'extract_duration', False),
                     ('isolationDuration', 'cleanup_duration', False),
                     ('irradiationName', 'irradiation', False),
                     ('mdfValue', '', False),
                     ('mdfValueSigma', '', False),
                     ('mdfLawApplied', '', False),
                     ('mdf40Ar36ArStandardRatio', '', False),
                     ('mdf40Ar36ArStandardRatioSigma', '', False),
                     ('fraction40ArRadiogenic', '', False),
                     ('fraction39ArPotassium', '', False),
                     ('measuredAge', 'age', True),
                     ('measuredAgeSigma', 'age_err_wo_j', True),
                     ('measuredKCaRatio', '', False),
                     ('measuredKCaRatioSigma', '', False),
                     ('measuredKClRatio', '', False),
                     ('measuredKClRatioSigma', '', False),

                     ('correctedTotal40Ar39ArRatio', '', False),
                     ('correctedTotal40Ar39ArRatioSigma', '', False),
                     ('correctedTotal37Ar39ArRatio', '', False),
                     ('correctedTotal37Ar39ArRatioSigma', '', False),
                     ('correctedTotal36Ar39ArRatio', '', False),
                     ('correctedTotal36Ar39ArRatioSigma', '', False),
                     ('corrected40ArRad39ArKRatio', '', False),
                     ('corrected40ArRad39ArKRatioSigma', '', False),
                     ('corrrected39ArK36ArAtmRatio', '', False),
                     ('corrrected39ArK36ArAtmRatioSigma', '', False),
                     ('corrrected40ArRadAtm36ArAtmRatio', '', False),
                     ('corrrected40ArRadAtm36ArAtmRatioSigma', '', False),
                     ('corrrected39ArK40ArRadAtmRatio', '', False),
                     ('corrrected39ArK40ArRadAtmRatioSigma', '', False),
                     ('corrrected36ArAtm40ArRadAtmRatio', '', False),
                     ('corrrected36ArAtm40ArRadAtmRatioSigma', '', False),
                     ('corrCoefficient4036over3936', '', False),
                     ('corrCoefficient3640over3940', '', False),
                     ('corrected36ArAtmospheric', '', False),
                     ('corrected36ArAtmosphericSigma', '', False),
                     ('corrected36ArCosmogenic', '', False),
                     ('corrected36ArCosmogenicSigma', '', False),
                     ('corrected36ArCalcium', '', False),
                     ('corrected36ArCalciumSigma', '', False),
                     ('corrected36ArChlorine', '', False),
                     ('corrected36ArChlorineSigma', '', False),
                     ('corrected37ArCalcium', '', False),
                     ('corrected37ArCalciumSigma', '', False),
                     ('corrected38ArAtmospheric', '', False),
                     ('corrected38ArAtmosphericSigma', '', False),
                     ('corrected38ArCosmogenic', '', False),
                     ('corrected38ArCosmogenicSigma', '', False),
                     ('corrected38ArCalcium', '', False),
                     ('corrected38ArCalciumSigma', '', False),
                     ('corrected38ArChlorine', '', False),
                     ('corrected38ArChlorineSigma', '', False),
                     ('corrected38ArPotassium', '', False),
                     ('corrected38ArPotassiumSigma', '', False),
                     ('corrected39ArCalcium', '', False),
                     ('corrected39ArCalciumSigma', '', False),
                     ('corrected39ArPotassium', '', False),
                     ('corrected39ArPotassiumSigma', '', False),
                     ('corrected40ArAtmospheric', '', False),
                     ('corrected40ArAtmosphericSigma', '', False),
                     ('corrected40ArCosmogenic', '', False),
                     ('corrected40ArCosmogenicSigma', '', False),
                     ('corrected40ArPotassium', '', False),
                     ('corrected40ArPotassiumSigma', '', False),
                     ('corrected40ArRadiogenic', '', False),
                     ('corrected40ArRadiogenicSigma', '', False),
                     ('measurementDescription', '', False))

INTERCEPT_ATTRS = (('intercept36Ar', '', True),
                   ('intercept36ArSigma', '', True),
                   ('intercept36ArRegressionType', '', False),
                   ('intercept37Ar', '', True),
                   ('intercept37ArSigma', '', True),
                   ('intercept37ArRegressionType', '', False),
                   ('intercept38Ar', '', True),
                   ('intercept38ArSigma', '', True),
                   ('intercept38ArRegressionType', '', False),
                   ('intercept39Ar', '', True),
                   ('intercept39ArSigma', '', True),
                   ('intercept39ArRegressionType', '', False),
                   ('intercept40Ar', '', True),
                   ('intercept40ArSigma', '', True),
                   ('intercept40ArRegressionType', '', False),
                   ('interceptUnit', '', False))

BLANK_ATTRS = (('blank36Ar', '', False),
               ('blank36ArSigma', '', False),
               ('blank37Ar', '', False),
               ('blank37ArSigma', '', False),
               ('blank38Ar', '', False),
               ('blank38ArSigma', '', False),
               ('blank39Ar', '', False),
               ('blank39ArSigma', '', False),
               ('blank40Ar', '', False),
               ('blank40ArSigma', '', False),
               ('blankUnit', '', False),)
# ============= EOF =============================================
