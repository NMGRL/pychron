# ===============================================================================
# Copyright 2016 Jake Ross
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
from traits.api import HasTraits, Str, Property, Instance
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.processing.isotope_group import IsotopeGroup


class AutomatedRunResult(HasTraits):
    runid = Str

    isotope_group = Instance(IsotopeGroup)
    summary = Property

    def _get_summary(self):
        return '''RUNID= {}
{}

{}'''.format(self.runid,
             self._intensities(),
             self._make_summary())

    def _make_summary(self):
        pass

    def _intensities(self):
        def fformat(s, n=5):
            return '{{:0.{}f}}'.format(n).format(s)

        names = 'Iso.', 'Det.', 'Intensity', 'Intercept', 'Baseline', 'Blank'

        lines = [self._make_header('Isotopes'),
                 '{:<6s}{:<8s}{:<25s}{:<25s}{:<25s}{:<25s}'.format(*names)]
        for k in self.isotope_group.isotope_keys:
            iso = self.isotope_group.isotopes[k]
            line = '{:<6s}{:<8s}{:<25s}{:<25s}{:<25s}{:<25s}'.format(k, iso.detector,
                                                                     fformat(iso.get_intensity()),
                                                                     fformat(iso.uvalue),
                                                                     fformat(iso.baseline.uvalue),
                                                                     fformat(iso.blank.uvalue))
            lines.append(line)
        return '\n'.join(lines)

    def _air_ratio(self):
        lines = [self._make_header('Ratios'),
                 'Ar40/Ar36= {:0.5f}'.format(self.isotope_group.get_ratio('Ar40/Ar36', non_ic_corr=True)),
                 'Ar40/Ar38= {:0.5f}'.format(self.isotope_group.get_ratio('Ar40/Ar38', non_ic_corr=True))]

        return '\n'.join(lines)

    def _make_header(self, h):
        return '============================={}{}'.format(h, '=' * (30 - len(h)))


class AirResult(AutomatedRunResult):
    def _make_summary(self):
        s = self._air_ratio()
        return s


class UnknownResult(AutomatedRunResult):
    def _make_summary(self):
        lines = ['===========================Summary===============================',
                 'AGE= {:0.4f}'.format(self.isotope_group.age)]
        return '\n'.join(lines)


class BlankResult(AutomatedRunResult):
    def _make_summary(self):
        s = self._air_ratio()
        return s

# if __name__ == '__main__':
#     ig = IsotopeGroup()
#     a40 = Isotope('Ar40', 'H1')
#     a40.set_uvalue((50000.12345, 0.4123412341))
#     a36 = Isotope('Ar36', 'CDD')
#     a36.set_uvalue((51230.12345 / 295.5, 0.132142341))
#
#     a38 = Isotope('Ar38', 'L1')
#     a38.set_uvalue((51230.12345 / 1590.5, 0.132142341))
#
#     ig.isotopes = dict(Ar40=a40, Ar36=a36, Ar38=a38)
#     ig.age = 1.143
#     a = AirResult(runid='1234123-01A',
#                   isotope_group=ig)
#     a.configure_traits()
# ============= EOF =============================================
