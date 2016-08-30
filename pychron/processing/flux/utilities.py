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
# ============= standard library imports ========================
# ============= local library imports  ==========================
from uncertainties import nominal_value, std_dev

from pychron.core.stats import calculate_weighted_mean, calculate_mswd
from pychron.processing.argon_calculations import calculate_flux


def mean_j(ans, error_kind, monitor_age, lambda_k):
    # ufs = (ai.uF for ai in ans)
    # fs, es = zip(*((fi.nominal_value, fi.std_dev)
    #                for fi in ufs))
    fs = [nominal_value(ai.uF) for ai in ans]
    es = [std_dev(ai.uF) for ai in ans]

    av, werr = calculate_weighted_mean(fs, es)

    if error_kind == 'SD':
        n = len(fs)
        werr = (sum((av - fs) ** 2) / (n - 1)) ** 0.5
    elif error_kind == 'SEM, but if MSWD>1 use SEM * sqrt(MSWD)':
        mswd = calculate_mswd(fs, es)
        werr *= (mswd ** 0.5 if mswd > 1 else 1)

    # reg.trait_set(ys=fs, yserr=es)
    # uf = (reg.predict([0]), reg.predict_error([0]))
    uf = (av, werr)
    j = calculate_flux(uf, monitor_age, lambda_k=lambda_k)
    # print age_equation(j, uf, lambda_k=lambda_k, scalar=1)
    mswd = calculate_mswd(fs, es)
    return j, mswd

# def calculate_flux(error_kind, monitor_age):
#
#     # helper funcs
#
#
#
#     # refs = self.references_pane.items
#
#     # ans, tcs = zip(*[db.get_labnumber_analyses(ri.identifier, omit_key='omit_ideo')
#     #                  for ri in refs])
#     # lns = [ri.identifier for ri in refs]
#     # tcs = db.get_labnumber_analyses(lns, omit_key='omit_ideo', count_only=True)
#     # prog = proc.open_progress(n=tcs, close_at_end=False)
#
#     # geom = self._get_geometry()
#     # editor = self.active_editor
#     # editor.geometry = geom
#     # editor.suppress_update = True
#
#     for ri in refs:
#         # ais, n = db.get_labnumber_analyses(ri.identifier, omit_key='omit_ideo')
#         # if n:
#         ref = ais[0]
#         sj = ref.labnumber.selected_flux_history.flux.j
#         sjerr = ref.labnumber.selected_flux_history.flux.j_err
#
#         ident = ref.labnumber.identifier
#
#         aa = proc.make_analyses(ais, progress=prog, calculate_age=True)
#         # n = len(aa)
#         dev = 100
#         # j = 0
#         # if n:
#         j = mean_j(aa)
#
#         if sj:
#             dev = (j.nominal_value - sj) / sj * 100
#
#         # if editor.tool.save_mean_j:
#         #     db.save_flux(ident, j.nominal_value, j.std_dev, inform=False)
#         #     sj, sjerr = j.nominal_value, j.std_dev
#
#         d = dict(saved_j=sj, saved_jerr=sjerr,
#                  mean_j=nominal_value(j), mean_jerr=std_dev(j),
#                  dev=dev, n=n, use=True)
#
#             # editor.set_position_j(ident, **d)
#             # if editor.tool.auto_clear_cache:
#             #     proc.remove_from_cache(aa)

# ============= EOF =============================================
