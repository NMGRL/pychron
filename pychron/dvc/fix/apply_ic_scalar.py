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
import os

from uncertainties import nominal_value, std_dev, ufloat

from pychron.core.helpers.iterfuncs import groupby_key, groupby_repo
from pychron.dvc import analysis_path, _analysis_path, dvc_load, dvc_dump
from pychron.dvc.dvc_orm import AnalysisTbl
from pychron.dvc.dvc_helper import get_dvc
from pychron.paths import paths

dvc = get_dvc()


# dvc = None


def get_analyses():
    # get low post and high post of A-02-J and A-02-Få

    hpost = "2020-11-04 17:39:19"
    # hpost = '2018-11-04 17:39:19'
    lpost = "2017-12-05 14:05:48"

    ans = dvc.get_analyses_by_date_range(
        lpost, hpost, analysis_types=("unknown",), verbose=True
    )

    return groupby_repo(ans)


def main():
    scalar = 293.5 / 295.5

    if dvc:
        dvc.create_session()

    # get analyses
    for repo, ans in get_analyses():
        repo_root = os.path.join(paths.repository_dataset_dir, repo)
        if os.path.isdir(repo_root):
            continue

        print("repository={}".format(repo))
        if dvc:
            dvc.clone_repository(repo, "https://github.com/NMGRLData/{}".format(repo))

        dvc.branch_repo(repo, "ic_factor_fix")
        ans = list(ans)
        for a in ans:
            set_ic_factor(repo, a, ("CDD", "L2(CDD)"), scalar)

        if dvc:
            dvc.update_analyses(
                ans,
                "icfactors",
                "<ICFactor> bulk edit scaled icfactor by {}".format(scalar),
            )

    if dvc:
        dvc.close_session()


def set_ic_factor(repo, analysis, target_det, scalar):
    p = analysis_path((analysis.uuid, analysis.record_id), repo, modifier="icfactors")
    if p:
        jd = dvc_load(p)

        for key, v in jd.items():
            if isinstance(v, dict):
                vv, ee = v["value"] or 0, v["error"] or 0
                if key in target_det:
                    nv = ufloat(vv, ee) * scalar
                    jd[key] = {
                        "value": nominal_value(nv),
                        "error": std_dev(nv),
                        "scalar": scalar,
                        "reviewed": True,
                        "fit": "bulk_edit",
                        "references": "",
                    }

        dvc_dump(jd, p)


if __name__ == "__main__":
    main()
# ============= EOF =============================================
