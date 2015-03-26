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
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change
from traitsui.api import View, UItem, Item, HGroup, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================

class BaseRecordView(object):
    def __init__(self, name):
        self.name = name


class XMLProjectRecordView(BaseRecordView):
    pass


class XMLSpectrometerRecord(BaseRecordView):
    pass


class XMLIrradiationRecordView(BaseRecordView):
    pass


class XMLAnalysis(object):
    def __init__(self, elem):
        self.labnumber = XMLDummyLabnumber(elem.get('measurementNumber'))
        self.measurement = XMLMeasurement(elem)

        self.record_id = ''
        self.aliquot = 0
        self.step = ''
        self.increment = 0
        self.uuid = self.labnumber
        self.tag = ''
        ds = elem.get('measurementDateTime')
        self.analysis_timestamp = datetime.strptime(ds, '%Y:%m:%d:%H:%M:%S.00')

class XMLMeasurement(object):
    def __init__(self, elem):
        pass


class XMLDummySample(object):
    def __init__(self, elem):
        self.name = 'fooboar'
        self.project = 'asdfasfd'


class XMLDummyLabnumber(object):
    def __init__(self, elem):
        self.identifier = elem
        self.sample = XMLDummySample(elem)
        self.irradiation_position = XMLIrradiationPosition(elem)


class XMLLabnumber(object):
    def __init__(self, elem):
        self.identifier = elem.get('igsn')

        pos = XMLIrradiationPosition(elem)
        self.irradiation_position = pos
        self.sample = XMLSample(elem)


class XMLSample(object):
    def __init__(self, elem):
        self.name = elem.get('sampleID')
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



