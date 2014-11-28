# ===============================================================================
# Copyright 2013 Jake Ross
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

#============= enthought library imports =======================
from traits.api import HasTraits, Bool, Str, Float, Int, Enum
from traitsui.api import View, HGroup, UItem, EnumEditor

from pychron.pychron_constants import NULL_STR, FIT_TYPES


#============= standard library imports ========================
#============= local library imports  ==========================

class Detector(HasTraits):
    fit = Str
    use = Bool
    label = Str
    ref = Bool
    isotope = Str
    isotopes = [NULL_STR, 'Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36']

    def traits_view(self):
        v = View(HGroup(
            UItem('use'),
            UItem('label',
                  width=-30,
                  style='readonly'),
            UItem('isotope',
                  editor=EnumEditor(name='isotopes'),
                  enabled_when='use'),
            UItem('fit',
                  enabled_when='use',
                  editor=EnumEditor(values=[NULL_STR] + FIT_TYPES))
        )
        )
        return v

    def _use_changed(self):
        if self.use and not self.fit:
            self.fit = 'linear'


class MeasurementConditional(HasTraits):
    name = Str
    use = Bool
    key = Enum('age', )
    comparator = Enum('<', '>', '<=', '>=')
    criterion = Float(enter_set=True, auto_set=False)
    start_count = Int(enter_set=True, auto_set=False)
    frequency = Int(enter_set=True, auto_set=False)

    def to_string(self):
        return "({}, ('{}','{}',{},{},{}))".format(self.use,
                                                   self.key,
                                                   self.comparator,
                                                   self.criterion,
                                                   self.start_count,
                                                   self.frequency)


class MeasurementAction(MeasurementConditional):
    action = Str
    resume = Bool(True)

    def to_string(self):
        return "({}, ('{}','{}',{},{},{},'{}',{}))".format(self.use,
                                                           self.key,
                                                           self.comparator,
                                                           self.criterion,
                                                           self.start_count,
                                                           self.frequency,
                                                           self.action,
                                                           self.resume)


class MeasurementTruncation(MeasurementConditional):
    pass


class MeasurementTermination(MeasurementConditional):
    pass


DETORDER = ['H2', 'H1', 'AX', 'L1', 'L2', 'CDD']


class Hop(HasTraits):
    position = Str
    detectors = Str
    counts = Int

    def to_string(self):
        if not (self.position and self.detectors and self.counts):
            return

        import string

        rpos = self.position
        k = ''
        for pii in rpos:
            if pii in string.ascii_letters:
                k += pii

        rrpos = rpos
        for ai in string.ascii_letters:
            rrpos = rrpos.replace(ai, '')

        dets = self.detectors.split(',')
        rdet = dets[0]
        if not rdet in DETORDER:
            return

        refidx = DETORDER.index(rdet)

        poss = []
        for di in dets:
            di = di.strip()
            if not di in DETORDER:
                return

            moff = DETORDER.index(di)
            pos = int(rrpos) + refidx - moff
            pos = '{}{}'.format(k, pos)
            poss.append((pos, di))

        ss = []
        for i, (pi, di) in enumerate(poss):
            si = '{}:{}'.format(pi, di)
            if i < len(poss) - 1:
                si += ','
                si = '{:<10s}'.format(si)
            ss.append(si)
        ss = ''.join(ss)

        ss = "'{}',".format(ss)
        return "{:<30s}{}".format(ss, self.counts)

    def traits_view(self):
        v = View(HGroup(UItem('position', width=-60),
                        UItem('detectors', width=250),
                        UItem('counts', width=-60)
        )
        )
        return v

        # ============= EOF =============================================
