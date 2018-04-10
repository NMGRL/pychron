# ===============================================================================
# Copyright 2018 ross
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
import shutil

from pychron.dvc import analysis_path, dvc_load, dvc_dump


def fix_identifier(source_id, destination_id, root, repo, aliquots):
    for a in aliquots:
        src_id = '{}-{:02n}'.format(source_id, a)
        dest_id = '{}-{:02n}'.format(destination_id, a)

        sp = analysis_path(src_id, repo, root=root)
        dp = analysis_path(dest_id, repo, root=root)
        if not os.path.isfile(sp):
            continue

        jd = dvc_load(sp)
        jd['identifier'] = destination_id
        dvc_dump(jd, dp)

        print('{}>>{}'.format(sp, dp))
        for modifier in ('baselines', 'blanks', 'extraction',
                         'intercepts', 'icfactors', 'peakcenter', '.data'):
            sp = analysis_path(src_id, repo, modifier=modifier, root=root)
            dp = analysis_path(dest_id, repo, modifier=modifier, root=root)
            print('{}>>{}'.format(sp,dp))
            if os.path.isfile(sp):
                shutil.copy(sp, dp)

if __name__ == '__main__':
    fix_identifier('25943', '25938', '/Users/ross/PychronDev/data/.dvc/repositories/',
                   'Irradiation-NM-294',
                   aliquots=[1,2,3,4,5,6]
                   # aliquots=[1,]#2,3,4,5,6]
                   )

# ============= EOF =============================================
