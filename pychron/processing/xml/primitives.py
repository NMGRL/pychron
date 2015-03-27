# ===============================================================================
# Copyright 2015 Jake Ross
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
from datetime import datetime
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change, Instance
from traitsui.api import View, UItem, Item, HGroup, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.experiment.utilities.identifier import make_runid


class BaseRecordView(object):
    def __init__(self, name):
        self.name = name


class XMLProjectRecordView(BaseRecordView):
    pass


class XMLSpectrometerRecord(BaseRecordView):
    pass


class XMLIrradiationRecordView(BaseRecordView):
    pass


# -------------------------------------------------
class XMLMassSpectrometer(object):
    def __init__(self, elem):
        exp = elem.xpath('Parameters/Experiment')[0]

        self.name = exp.get('massSpectrometer')


class XMLMainView(HasTraits):
    def trait_context(self):
        return {'object': self.model}

    def traits_view(self):
        v = View(UItem('uuid'), UItem('analysis_timestamp'))
        return v


class XMLAnalysisView(HasTraits):
    main_view = Instance(XMLMainView)
    selection_tool = None

    def __init__(self, *args, **kw):
        super(XMLAnalysisView, self).__init__(*args, **kw)
        self.main_view=XMLMainView(model=self.model)
        print self.main_view

    def update_fontsize(self, a, s):
        pass

    def traits_view(self):
        v = View(UItem('main_view', style='custom'))
        return v

    def _main_view_default(self):
        mv = XMLMainView(model=self.model)
        return mv


class XMLAnalysis(HasTraits):
    selected_histories = None
    analysis_view = Instance(XMLAnalysisView)

    def __init__(self, elem, meas_elem):
        self.uuid = meas_elem.get('measurementNumber')
        self.labnumber = XMLLabnumber(elem)
        self.labnumber.identifier = self.uuid

        self.measurement = XMLMeasurement(elem, meas_elem)
        self.extraction = XMLExtraction(meas_elem)
        # self.record_id = ''
        self.aliquot = 0
        self.step = ''
        self.increment = 0
        self.tag = ''
        ds = meas_elem.get('measurementDateTime')
        self.analysis_timestamp = datetime.strptime(ds, '%Y:%m:%d:%H:%M:%S.00')

    def _analysis_view_default(self):
        return XMLAnalysisView(model=self, analysis_id=self.uuid)

    @property
    def record_id(self):
        return make_runid(self.uuid, self.aliquot, self.step)


class XMLExtraction(object):
    def __init__(self, meas_elem):
        self.extract_value = meas_elem.get('temperature')
        self.cleanup_duration = meas_elem.get('isolationDuration')
        self.extract_duration = 0


class XMLMeasurement(object):
    def __init__(self, elem, meas_elem):
        exp = elem
        self.mass_spectrometer = XMLMassSpectrometer(elem)


# class XMLDummySample(object):
# def __init__(self, elem):
# self.name = 'fooboar'
# self.project = 'asdfasfd'


# class XMLDummyLabnumber(object):
# def __init__(self, elem):
# self.identifier = elem
# self.sample = XMLDummySample(elem)
#         self.irradiation_position = XMLIrradiationPosition(elem)


class XMLLabnumber(object):
    selected_flux_id = None

    def __init__(self, elem):
        self.identifier = elem.get('igsn')
        pos = XMLIrradiationPosition(elem)
        self.irradiation_position = pos
        self.sample = XMLSample(elem)


class XMLSample(object):
    def __init__(self, elem):
        self.name = elem.get('sampleID')
        self.igsn = elem.get('igsn')

        self.lon = float(elem.get('longitude'))
        self.lat = float(elem.get('latitude'))
        exp = elem.xpath('Parameters/Experiment')[0]
        self.material = XMLMaterial(exp)
        self.project = XMLProject(exp)


class XMLMaterial(object):
    def __init__(self, exp_elem):
        self.name = exp_elem.get('sampleMaterialType')


class XMLProject(object):
    def __init__(self, exp_elem):
        self.name = exp_elem.get('projectName')


class XMLIrradiationPosition(object):
    def __init__(self, elem):
        self.position = '---'
        self.level = XMLIrradiationLevel(elem)


class XMLIrradiationLevel(object):
    def __init__(self, elem):
        self.name = ''
        self.irradiation = XMLIrradiation(elem)


class XMLIrradiation(object):
    def __init__(self, elem):
        self.name = 'Foo'

# ============= EOF =============================================



