# ===============================================================================
# Copyright 2020 ross
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
from uncertainties import nominal_value, std_dev, ufloat

from pychron.core.helpers.iterfuncs import groupby_key, groupby_repo
from pychron.dvc import analysis_path, _analysis_path, dvc_load
from pychron.dvc.dvc_orm import AnalysisTbl
from pychron.dvc.fix import get_dvc

dvc = get_dvc()
dvc = None


def get_analyses(dvc):
    lpost = ''
    hpost = ''

    ans = dvc.get_analyses_by_date_range(lpost, hpost)
    return groupby_repo(ans)


def main():
    det = 'CDD'
    scalar = 0.1

    if dvc:
        dvc.create_session()

    # get analyses
    for repo, ans in get_analyses(dvc.session):
        if dvc:
            dvc.open_repo(repo)
            dvc.smart_pull()

        ans = list(ans)
        for a in ans:
            set_ic_factor(repo, a, det, scalar)

        if dvc:
            dvc.update_analyses(ans, 'icfactors', '<ICFactor> bulk edit scaled icfactor by {}'.format(scalar))

    if dvc:
        dvc.close_session()


def set_ic_factor(repo, runid, target_det, scalar):
    p = _analysis_path(runid, repo, modifier='icfactors')
    jd = dvc_load(p)
    print('old', jd)
    for key, v in jd.items():
        if isinstance(v, dict):
            vv, ee = v['value'] or 0, v['error'] or 0
            if key == target_det:
                nv = ufloat(vv, ee) * scalar
                jd[key] = {'value': nominal_value(nv),
                           'error': std_dev(nv),
                           'reviewed': True,
                           'fit': 'bulk_edit',
                           'references': ''}

    print('new', jd)
    # dvc_dump(jd, path)


if __name__ == '__main__':
    main()
# ============= EOF =============================================
