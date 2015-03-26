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
import os
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change, List, Instance
from traitsui.api import View, UItem, Item, HGroup, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.xml.xml_parser import XMLParser
from pychron.loggable import Loggable


class MockSession(object):
    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class BaseRecordView(object):
    def __init__(self, name):
        self.name = name


class XMLProjectRecordView(BaseRecordView):
    pass


class XMLSpectrometerRecord(BaseRecordView):
    pass


class XMLIrradiationRecordView(BaseRecordView):
    pass


class XMLDatabase(Loggable):
    kind = None
    path = Str

    projects = List
    samples = List
    irradiations =List
    mass_spectrometers = List

    _parser = Instance(XMLParser)

    def _path_changed(self, new):
        self.datasource_url = 'Invalid Path'
        if new:
            if os.path.isfile(new):
                self.datasource_url = os.path.join(os.path.basename(os.path.dirname(new)), os.path.basename(new))

                self._parser = XMLParser(new)

                self._load_projects()
                self._load_mass_spectrometers()
                self._load_irradiations()

                self._load_sample_meta()

    def session_ctx(self, *args, **kw):
        return MockSession()

    def get_projects(self, *args, **kw):
        return self.projects

    def get_mass_spectrometers(self):
        return self.mass_spectrometers

    def get_irradiations(self, *args, **kw):
        return self.irradiations

    def _load_projects(self):
        elem = self._parser.get_elements('Parameters/Experiment')
        self.projects = [XMLProjectRecordView(i.get('projectName')) for i in elem]

    def _load_irradiations(self):
        elem = self._parser.get_elements('Parameters/Experiment/Irradiation')
        self.irradiations = [XMLIrradiationRecordView(i.get('irradiationName')) for i in elem]

    def _load_mass_spectrometers(self):
        elem = self._parser.get_elements('Parameters/Experiment')
        self.mass_spectrometers = [XMLSpectrometerRecord(i.get('massSpectrometer')) for i in elem]

    def _load_sample_meta(self):
        elem = self._parser.get_elements('Sample')
        pass

# ============= EOF =============================================



