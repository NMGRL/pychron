# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from traits.api import HasTraits, Str, Instance
# ============= standard library imports ========================
import time
import os
from numpy import linspace, polyfit
# ============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.paths import paths
from pychron.core.helpers.parsers.learner_parser import LearnerParser

class LearnerValve(HasTraits):
    name = Str
    _start_time = None
    _stop_time = None
    _duration = 0
    def startTime(self):
        self._start_time = time.time()

    def stopTime(self):
        if self._start_time:
            self._stop_time = time.time()
            self._duration = self._stop_time - self._start_time
            self._start_time = None

KINDDICT = {'None':0, 'GP50':1, 'D50':2, 'NP10':3}
SPECDICT = {'obama':0, 'jan':1}
HOTCOLDDICT = {'cold':0, 'hot':1}
MATERIALDICT = {'sanidine':0, 'groundmass':1}

class LearnerGetter(HasTraits):
    valve = Instance(LearnerValve)
    name = Str
    _kind = None
    _spectrometer = None
    _hotcold = None
    # kind = Str
    @property
    def duration(self):
        if self.valve is not None:
            return self.valve._duration

    def setkind(self, v):
        self._kind = v

    def getkind(self):
        return KINDDICT[self._kind]

#    def setspectrometer(self, v):
#        self._spectrometer = v
#
#    def getspectrometer(self):
#        return SPECDICT[self._spectrometer]

    def sethotcold(self, v):
        self._hotcold = v

    def gethotcold(self):
        return HOTCOLDDICT[self._hotcold]

    kind = property(fset=setkind,
                  fget=getkind)
#    spectrometer = property(fset=setspectrometer,
#                          fget=getspectrometer)
    hotcold = property(fset=sethotcold,
                  fget=gethotcold)

#    @property
#    def kind(self, v):
#        self._kind = v
#        return self._kind

class ExtractionLineLearner(Loggable):
#    def __init__(self, manager, *args, **kw):
#        super(ExtractionLineSnooper, self).__init__(*args, **kw)
#
#        #register trait changes
#        manager.on
#    configuration = None
    getters = None
    valves = None

    def load_configuration(self):
        self.getters = dict()
        self.valves = dict()
        p = os.path.join(paths.setup_dir, 'learner.xml')
        if os.path.isfile(p):
            cp = LearnerParser(p)
            for gi in cp.get_getters():
                g = self._getter_factory(gi)
                self.getters[g.name] = g

    def _getter_factory(self, gi):
        valve = gi.find('valve')
        vname = valve.text.strip()
        if self.valves.has_key(vname):
            v = self.valves[vname]
        else:
            v = self._valve_factory(valve)

        g = LearnerGetter(name=gi.text.strip(),
                          kind=gi.find('kind').text.strip(),
#                          spectrometer=gi.find('spectrometer').text.strip(),
                          hotcold=gi.find('hotcold').text.strip(),
                          valve=v)
        return g

    def _valve_factory(self, valve):
        v = LearnerValve(name=valve.text.strip())
        self.valves[v.name] = v
        return v

    def open_close_valve(self, name, action, result):
        if self.getters:
            # find valve in configuration
            getter = self._get_getter_by_valve(name)
#            print 'open', getter
            if getter:
                v = getter.valve
                if action == 'open' and result:
                    v.startTime()
                else:
                    v.stopTime()

    def _get_getter_by_valve(self, n):
        return next((c for c in self.getters.values()
                            if c.valve.name == n), None)

    def _get_getter(self, n):
        return next((c for c in self.getters.values()
                            if c.name == n), None)

    def get_duration(self, name):
        getter = self._get_getter(name)
        return getter.duration

    def _get_time_intensity_data(self, key):
        x = linspace(10, 200)
        y = -10 * x + 3000
        return x, y

    def _calculate_delta(self, x, y, lim=50):
        iLim = polyfit(x[:lim], y[:lim], 1)[-1]
        iN = polyfit(x, y, 2)[-1]

        return iN, iLim / iN

    def _get_isotopic_data(self):
        isos = []
        deltas = []
        for iso in [40, 39, 37, 36]:
            key = 'ar{}'.format(iso)
            data = self._get_time_intensity_data(key)
            signal, delta = self._calculate_delta(*data)
            isos.append(signal)
            deltas.append(delta)

        return isos, deltas

    def write_result(self):
        getters = ['BoneGP50', 'BoneD50', 'BoneNP10' ]
        data = []
        spec = 'obama'
        mass = 25.32
        material = 'groundmass'

        # write the getter info
        for gi in getters:
            g = self._get_getter(gi)
            data += [g.kind, g.duration, g.hotcold]

        # write the exp setup info
        data += SPECDICT[spec], MATERIALDICT[material], mass
        signals, deltas = self._get_isotopic_data()
        data += signals + deltas
        # write the results info

        print data
        return data


# ===============================================================================
# testing
# ===============================================================================
from unittest import TestCase

class ELLearnerTestCase(TestCase):
    def setUp(self):
        self.learner = ExtractionLineLearner()
        self.learner.load_configuration()

    def testLoadConfig(self):
        g = self.learner.getters
        self.assertEqual(len(g.keys()), 3)

        v = self.learner.valves
        self.assertEqual(len(v.keys()), 3)

    def testOpen(self):
        n = 0.25
        name = 'G'
        self._prep(n, name)

        d = self.learner.get_duration('BoneGP50')
        self.assertGreaterEqual(d, n)

    def testWriting(self):
        n = 0.25
        name = 'G'
        self._prep(n, name)

        r = self.learner.write_result()

        self.assertEqual(len(r), 20)

    def _prep(self, n, name):
        self.learner.open_close_valve(name, 'open', True)
        time.sleep(n)
        self.learner.open_close_valve(name, 'close', True)


# ============= EOF =============================================
