# ===============================================================================
# Copyright 2017 ross
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
from datetime import datetime

from numpy import array

from pychron.data_mapper.sources.file_source import FileSource
from pychron.data_mapper.sources.nice_parser import NiceParser
from pychron.processing.isotope import Isotope
from pychron.processing.isotope_group import IsotopeGroup


class NuFileSource(FileSource):
    def get_analysis_import_spec(self, p, pnice, delimiter=None):
        f = self.file_gen(p, delimiter)
        pspec = self.new_persistence_spec()
        rspec = pspec.run_spec

        version = next(f)
        ncycles = next(f)
        total_analysis_time = int(next(f)[1])
        start = next(f)
        end = next(f)
        nzeros = next(f)
        nanalysis_cycles = next(f)
        toffset = next(f)

        ts = next(f)[1]
        rspec.analysis_timestamp = datetime.strptime(ts, '#%Y-%m-%d %H:%M:%S#')

        collector_gains = next(f)

        int_posts = [next(f) for i in xrange(41)]
        npeakscentered = next(f)
        ndeflectors = next(f)[1]
        source_ht = next(f)
        half_plate_v = next(f)
        trap = next(f)
        trap_voltage = next(f)
        repeller = next(f)
        filament_v = next(f)
        delta_hp = next(f)
        z_lens = next(f)
        delta_z = next(f)
        max_current = next(f)
        quad_1 = next(f)
        cubic_1 = next(f)
        lin_1 = next(f)
        q18_cor = next(f)
        q19_cor = next(f)
        quad_2 = next(f)
        cubic_2 = next(f)
        lin_2 = next(f)
        q28_cor = next(f)
        q29_cor = next(f)
        suppressor = next(f)
        Deflect_IC1 = next(f)
        Filter_IC0 = next(f)
        Deflect_IC0 = next(f)
        Deflect_IC2 = next(f)
        Filter_IC3 = next(f)
        Deflect_IC3 = next(f)
        mdfpath = next(f)
        _ = next(f)
        ics = next(f)
        discs = next(f)

        [_ for _ in xrange(9)]

        signals = []
        for _ in xrange(total_analysis_time):
            line = next(f)
            _type = int(line[-1])

            if _type:
                signals.append(map(float, line))

        signals = array(signals)

        with open(pnice, 'r') as nice:

            isotopes = {}
            parser = NiceParser(signals)
            for line in nice:
                try:
                    lhs, rhs = map(str.strip, line.split('='))
                except ValueError:
                    continue

                if lhs.startswith('Result'):
                    break

                parser.set_tokens(rhs.split(' '))

                ret, det_idx = parser.exp()

                iso = Isotope(lhs, 'IC{}'.format(det_idx))
                iso.name = lhs
                iso.xs = ret.xs
                iso.ys = ret.ys

                isotopes[lhs] = iso

        pspec.isotope_group = IsotopeGroup(isotopes=isotopes)
        return pspec


# ============= EOF =============================================
