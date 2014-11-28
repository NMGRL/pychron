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

from traits.etsconfig.etsconfig import ETSConfig
ETSConfig.toolkit = 'qt4'

from traits.api import HasTraits, Instance, Float, on_trait_change, Int, Str, \
    Bool
from traitsui.api import View, Item, UItem, HGroup, VGroup
from numpy import linspace, polyfit, polyval, where, hstack, exp, ones_like
# from pylab import *
from pychron.processing.argon_calculations import age_equation, calculate_flux
from pychron.graph.stacked_graph import StackedGraph
#============= standard library imports ========================
#============= local library imports  ==========================
class Iso(HasTraits):
    name = Str
    intensity = Float
    equil_rate = Float
    static_rate = Float
    def traits_view(self):
        v = View(HGroup(UItem('name', style='readonly'), Item('intensity'),
                      Item('equil_rate'), Item('static_rate')))
        return v

class EquilibrationInspector(HasTraits):
    graph = Instance(StackedGraph, ())

    Ar40 = Instance(Iso, {'name':'Ar40',
                          'intensity':3000,
                          'equil_rate':0.0001,
                          'static_rate':0.0002
                          }
                    )
    Ar39 = Instance(Iso, {'name':'Ar39',
                          'intensity':230,
                          'equil_rate':0.0001,
                          'static_rate':0.0002
                          }
                    )

    max_time = Int(50)
    vary_time_zero = Bool(True)

    def traits_view(self):
        cntrl_grp = VGroup(
                           UItem('Ar40', style='custom'),
                           UItem('Ar39', style='custom'),
#                            HGroup(Item('Ar40'),
#                                Item('Ar39'),
#                                ),
                           HGroup(Item('max_time'), Item('vary_time_zero'))
#                            Item('pump_rate')
                           )

        v = View(
                 VGroup(
                        cntrl_grp,
                        UItem('graph', style='custom')
                        ),
                 title='Equilibration Inspector'
                 )

        return v

    def refresh(self):
        self._rebuild_graph()

    @on_trait_change('Ar+:[], max_time, vary_time_zero')
    def _update_graph(self, name, new):
        self._rebuild_graph()

    def calc_intercept(self, mag, post, eq_rate, static_rate, xma, plotid,
                       time_zero=0):
        '''
            post: inlet close time in seconds after eq start
        '''

        def func(t):
            I_el = EL_src(mag, t, post)
            I = I_el + MS_src(t) - \
                MS_pump(t, I_el, post, eq_rate, static_rate)
            return I

        ts = linspace(0, xma, xma + 1)
        I = func(ts)

        g = self.graph
#         g.new_series(ts, I, plotid=plotid, color='black')
        fidx = where(ts > post)[0]
        b = 1
        if fidx.shape[0]:
            g.new_series(ts[:fidx[0]], I[:fidx[0]], plotid=plotid, color='black')
            g.new_series(ts[fidx[0]:], I[fidx[0]:], plotid=plotid, color='red')
    #         plot(ts[:fidx[0]], I[:fidx[0]], 'black')
            fI = I[fidx]
            ft = ts[fidx]
            m, b = polyfit(ft, fI, 1)
            vi = fI[0]
            b = vi - m * post

#             g.new_series(ts, polyval((m, b), ts), plotid=plotid, color='red',
#                         line_style='dash')

#         plot(ts, polyval((m, b), ts), ls='--', c='r')


        return polyval((m, b), time_zero)

    def _rebuild_graph(self):
        g = self.graph
        g.clear()
        plot1 = g.new_plot(ytitle='Delta Age (ka)',
                           xtitle='Time (s)',
                           padding_left=70,
                           padding_right=25
                           )
        plot2 = g.new_plot(ytitle='Ar39 (fA)',
                           padding_left=70,
                           padding_right=25
                           )
        plot3 = g.new_plot(ytitle='Ar40 (fA)',
                           padding_left=70,
                           padding_right=25
                           )

        Ar40 = self.Ar40.intensity
        Ar39 = self.Ar39.intensity

        if not (Ar40 and Ar39):
            return

        plot2.value_range.low_setting = Ar39 * .95
        plot2.value_range.high_setting = Ar39 * 1.05

        plot3.value_range.low_setting = Ar40 * .95
        plot3.value_range.high_setting = Ar40 * 1.01

        R = Ar40 / Ar39

        xma = self.max_time

        rs = []
        ns = []
        ds = []

        if self.vary_time_zero:
            posts = (15,)
            xs = range(0, 15)
            index = xs
        else:
            posts = range(5, 30)
            xs = (0,)
            index = posts

        for pi in posts:
            for ti in xs:
    #             subplot(311)
                n = self.calc_intercept(Ar40, pi,
                                        self.Ar40.equil_rate,
                                        self.Ar40.static_rate,
                                        xma, 2,
                                        time_zero=ti
                                        )
    #             subplot(312)
                d = self.calc_intercept(Ar39, pi,
                                        self.Ar39.equil_rate,
                                        self.Ar39.static_rate,
                                        xma, 1,
                                        time_zero=ti)

                ns.append(n)
                ds.append(d)
    #             rs.append(((n / d) - R) / R * 100)
                rs.append((n / d))

#         print ns
#         g.new_series(xs, ns, plotid=2)
#         g.new_series(xs, ds, plotid=1)
#         g.new_series(to, rs, plotid=0)

        mon_age = 28
        j = calculate_flux((Ar40, 0), (Ar39, 0), mon_age)
        ages = [(age_equation(j[0], abs(ri)) - mon_age) * 1000 for ri in rs]
        g.new_series(index, ages, plotid=0)

def EL_src(mag, t, post, rate=0.8):
    pre_t = where(t <= post)[0]
    post_t = where(t > post)[0]

    pre_v = mag * (1 - exp(-rate * t[pre_t]))

    return hstack((pre_v, ones_like(post_t) * pre_v[-1]))


def MS_src(t, rate=0.0125):
    return rate * t

def MS_pump(t, mag_t, post, eq_rate, static_rate):
    pre_t = where(t <= post)[0]
    post_t = where(t > post)[0]
    pre_v = eq_rate * t[pre_t] * mag_t[pre_t]
    post_v = static_rate * t[post_t] * mag_t[post_t]
    return hstack((pre_v, post_v))

# def calc_intercept(intensity, post, pump_rate, xma):
#     '''
#         post: inlet close time in seconds after eq start
#     '''
#     def func(t):
#         I_el = EL_src(intensity, t, post)
#         I = I_el + MS_src(t) - \
#             MS_pump(t, I_el, post, rate=pump_rate)
#         return I
#
#     ts = linspace(0, xma, 500)
#     I = func(ts)
#
#     fidx = where(ts > post)[0]
#
#     plot(ts[:fidx[0]], I[:fidx[0]], 'black')
#     fI = I[fidx]
#     ft = ts[fidx]
#     m, b = polyfit(ft, fI, 1)
#     vi = fI[0]
#     b = vi - m * post
#
#     plot(ts, polyval((m, b), ts), ls='--', c='r')
#     return b
#
# def main():
#
# #     coctail ratio
# #     Ar39 = 250 / 4.
# #     Ar40 = 13.8 * Ar39
#     Ar40 = 300
#     Ar39 = 5
#
#
#     xma = 150
#     pump_rate = 0.0001
#
# #     to = range(5, 20)
# #     to = (1, 3, 5, 10, 15, 20, 30, 35)
#     to = (1, 5, 10, 15, 20)
#     rs = []
# #     to = range(1, 200, 10)
#     for i, pi in enumerate(to):
#         subplot(311)
#         n = calc_intercept(Ar40, pi, pump_rate, xma)
#         subplot(312)
#         d = calc_intercept(Ar39, pi, pump_rate, xma)
#         rs.append((n / d))
#
#     subplots_adjust(hspace=0.05)
#     subplot(311)
#     xlim(0, xma)
#     xticks(visible=False)
#     ylabel('Ar40 fA')
#
#     subplot(312)
#     xlim(0, xma)
#     xticks(visible=False)
#     ylabel('Ar39 fA')
#
#     mon_age = 28
#     j = calculate_flux((Ar40, 0), (Ar39, 0), mon_age)
#     ages = [(age_equation(j[0], abs(ri)) - mon_age) * 1000 for ri in rs]
#
#     subplot(313)
#     plot(to, ages)
#     xlim(0, xma)
#     ylabel('delta age (ka) ')
#     xlabel('t (s)')
#
#     show()

if __name__ == '__main__':



    eq = EquilibrationInspector()
    eq.Ar40.intensity = 300
    eq.Ar39.intensity = 25
    eq.configure_traits()
#     main()
# ============= EOF =============================================
