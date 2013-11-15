#===============================================================================
# Copyright 2011 Jake Ross
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
#===============================================================================



from traits.api import Instance
from traitsui.api import View, Item
from pychron.graph.graph import Graph
from uncertainties import ufloat
import csv
from pychron.stats import calculate_mswd, calculate_weighted_mean
# KEYS36 = ['one36', 'two36', 'three36', 'four36', 'five36', 'six36']
# KEYS40 = ['one40', 'two40', 'three40', 'four40', 'five40', 'six40']
KEYS = ['one', 'two', 'three', 'four', 'five']
KEYS40 = ['{}40'.format(k) for k in KEYS]
KEYS36 = ['{}36'.format(k) for k in KEYS]


class DeadTime():
    '''    
    '''

    def read_csv(self):

        p = '/Users/ross/Desktop/deadtime_full_obama'
        # p = '/Users/ross/Desktop/deadtime_jan2'
        f = open(p, 'U')
        reader = csv.reader(f, delimiter='\t')

        header = reader.next()

        ind36 = header.index('Ar36_')
        ind40 = header.index('Ar40_')
        rsind = header.index('Run Script')

        nshots = dict(one36=[],
                      two36=[],
                      three36=[],
                      four36=[],
                      five36=[],
                      six36=[],
                      one40=[],
                      two40=[],
                      three40=[],
                      four40=[],
                      five40=[],
                      six40=[]
        )
        for l in reader:
            if not l or l[0] == '':
                break

            rskey = KEYS36[int(l[rsind].strip()[-1]) - 1]
            uf = ufloat(float(l[ind36]) * 6240, float(l[ind36 + 1]) * 6240)
            nshots[rskey].append(uf)

            rskey = KEYS40[int(l[rsind].strip()[-1]) - 1]
            uf = ufloat(float(l[ind40]) * 6240, float(l[ind40 + 1]) * 6240)
            nshots[rskey].append(uf)

        return nshots

    def _correct_for_deadtime(self, nshots, k, tau):
        cor = []
        for cmeas in nshots[k]:
            ccor = cmeas / (1 - cmeas * tau)
            cor.append(ccor)

        nshots[k + 'cor'] = cor

    def _calculate_mean_ratio(self, s40, s36):

        r = [i40 / i36 for i40, i36 in zip(s40, s36)]

        v = [vi.nominal_value for vi in r]
        errs = [vi.std_dev for vi in r]

        m, e = calculate_weighted_mean(v, errs)

        return m, e


if __name__ == '__main__':
    from numpy import linspace, polyfit, polyval

    d = DeadTime()
    g = Graph()

    g.new_plot(padding=[30, 10, 20, 40])
    g.new_plot(padding=[30, 10, 20, 40], show_legend=True)
    nshots = d.read_csv()
    #    taus = range(5, 40, 5)
    taus = linspace(0, 30, 41)
    rratios1 = []
    mswds1 = []

    for i in KEYS:
        s40 = nshots[i + '40']
        s36 = nshots[i + '36']
        m1, _ = d._calculate_mean_ratio(s40, s36)
        print 'uncorrected ratio {} = {:0.2f} '.format(i, m1)

    for tau in taus:
    #        print 'calculating for dt= ', tau
        for k in KEYS36:
            d._correct_for_deadtime(nshots, k, tau / 1e9)

        x = range(1, 6)
        ratios1 = []
        errs1 = []
        for i in KEYS:
            m1, e1 = d._calculate_mean_ratio(nshots[i + '40'], nshots[i + '36cor'])
            ratios1.append(m1)
            errs1.append(e1)

        ms1 = calculate_mswd(ratios1, errs1)

        mswds1.append(ms1)

        rratios1.append(ratios1)

        if tau % 5 == 0:
            g.new_series(x, ratios1, plotid=1, type='line')
            i = int((tau / 5) - 1)
        #            g.set_series_label('p', plotid=1, series=i)
        #            g.set_series_label('{} (ns)'.format(tau), plotid=1, series=i)


        #    g.plots[1].legend.plots = dict([(k, v[0]) for k, v in g.plots[1].plots.iteritems()])
        #    print g.plots[1].legend.plots
    g.new_series(taus, mswds1, plotid=0, type='line_scatter')
    g.set_y_limits(min(mswds1) - 5, max(mswds1) + 5, plotid=0)

    # fit parabola and find minimum.
    coeffs1 = polyfit(taus, mswds1, 2)
    # min at dy=0   (ax2+bx+c)dx=dy==2ax+b
    # 2ax+b=0 , x=-b/(2a)
    dt = -coeffs1[1] / (2 * coeffs1[0])
    print 'dead time1= ', dt

    g.set_x_title('# Airshots', plotid=1)
    g.set_x_title('Dead Time (ns)', plotid=0)

    g.set_y_title('40Ar/36Ar', plotid=1)
    g.set_y_title('MSWD', plotid=0)

    g.add_vertical_rule(dt)
    #    g.add_plot_label('dead time (ns)= {:0.2f}'.format(dt), 235, 100)
    #    g.add_data_label('dead time (ns)= {:0.2f}'.format(dt), dt, 30, plotid=0)
    g.add_data_label(dt, polyval(coeffs1, dt), plotid=0)

    #    g.set_series_label('{} (ns)'.format(tau), plotid=1, series=0)
    g.configure_traits()

#======== EOF ================================
