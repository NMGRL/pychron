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

# ============= enthought library imports =======================
# from traits.api import HasTraits
# from traitsui.api import View, Item
# ============= standard library imports ========================
from numpy import average, array
# ============= local library imports  ==========================
from pychron.processing.tasks.smart_project.base_smarter import BaseSmarter
from pychron.processing.argon_calculations import calculate_flux
from itertools import groupby
from pychron.processing.tasks.flux.flux_pdf_writer import FluxPDFWriter

class SmartFlux(BaseSmarter):
    monitor_age = 28.02e6

    def save(self, p, ans, component):
        writer = FluxPDFWriter(monitor_age=self.monitor_age)
        writer.build(p, ans, component)

    def fit_irradiation(self, irradiation, levels=None, exclude=None):
        db = self.processor.db
        dbirrad = db.get_irradiation(irradiation)

        if levels is None:
            levels = dbirrad.levels

        for li in levels:
            if not li in exclude:
                self._fit_level(li)

    def fit_level(self, irradiation, level):
        db = self.processor.db
        dblevel = db.get_irradiation_level(irradiation, level)
        return self._fit_level(dblevel)

    def _fit_level(self, level):
        # get references and unknowns
        refs, unks = self.processor.group_level(level)

        # calculate new J values for the monitor holes
        refs = [refs.next()]
        return self._compute_js(refs)


    def _calculate_mean_j(self, ans, monitor_age):
        '''
            ans: [Analysis,...,]
            monitor_age: years
        '''
        def calc_j(ai):
            ar40 = ai.arar_result['rad40']
            ar39 = ai.arar_result['k39']
            return calculate_flux(ar40, ar39, monitor_age)

        js, errs = zip(*[calc_j(ai) for ai in ans])
        errs = array(errs)
        wts = errs ** -2
        m, ss = average(js, weights=wts, returned=True)
        return m, ss ** -0.5

    def _compute_js(self, monitors):
        monitors = list(monitors)
        mon_age = self.monitor_age
        proc = self.processor

        a = [ai for mi in monitors
                for ai in proc.db.get_analyses(lab_id=mi.labnumber.id,
                                       step='', status=0)]
        tans = proc.make_analyses(a)
        proc.load_analyses(tans)

        def get_monitor(li):
            return next((mi for mi in monitors
                            if mi.labnumber.identifier == li), None)

        for i, (ln, ans) in enumerate(groupby(tans, lambda x: x.labnumber)):
            ans = list(ans)
            for ai in ans:
                ai.group_id = i

            me, sd = self._calculate_mean_j(ans, mon_age)

            mi = get_monitor(ln)
            mi.j = me
            mi.j_err = sd

        return tans
        # plot the monitor analyses on an ideogram
        # @todo: use mi to get irradiation instead
#         irrad = proc.irradiation
#         level = proc.level

#         self._open_ideogram_editor(tans, name='Ideo - {}'.format(irrad, level))

#         reg2D, reg3D = self._model_flux(monitors)
#
#         for pp in unknowns + monitors:
#             x = math.atan2(pp.x, pp.y)
#             y = reg2D.predict(x)
#             pp.pred_j = y
#
#         self.regressor2D = reg2D
#         self.regressor3D = reg3D


# ============= EOF =============================================
