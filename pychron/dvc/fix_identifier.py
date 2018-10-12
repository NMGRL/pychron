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


def fix_identifier(source_id, destination_id, root, repo, aliquots, steps, dest_steps=None, dest_aliquots=None):

    if dest_aliquots is None:
        dest_aliquots = aliquots
    if dest_steps is None:
        dest_steps = steps

    # for a, da, step, dstep in zip(aliquots, dest_aliquots, steps, dest_steps):
    #     src_id = '{}-{:02n}{}'.format(source_id, a, step)
    #     dest_id = '{}-{:02n}{}'.format(destination_id, da, dstep)

def _fix_id(src_id, dest_id, identifier, root, repo):
        sp = analysis_path(src_id, repo, root=root)
        dp = analysis_path(dest_id, repo, root=root, mode='w')
        print(sp, dp)
        if not os.path.isfile(sp):
            print('not a file', sp)
            return

        jd = dvc_load(sp)
        jd['identifier'] = identifier
        dvc_dump(jd, dp)

        print('{}>>{}'.format(sp, dp))
        for modifier in ('baselines', 'blanks', 'extraction',
                         'intercepts', 'icfactors', 'peakcenter', '.data'):
            sp = analysis_path(src_id, repo, modifier=modifier, root=root)
            dp = analysis_path(dest_id, repo, modifier=modifier, root=root)
            print('{}>>{}'.format(sp,dp))
            if os.path.isfile(sp):
                # shutil.copy(sp, dp)
                shutil.move(sp,dp)


if __name__ == '__main__':
    root = '/Users/ross/PychronDev/data/.dvc/repositories/'
    repo = 'Saifuddeen01097'

    # fix_identifier('66340', '66431', '/Users/ross/PychronDev/data/.dvc/repositories/',
    #                'Saifuddeen01097',
    #                aliquots=[2],
    #                steps=['A','B']
    #                dest_aliquots=[1]
    #                # aliquots=[1,]#2,3,4,5,6]
    #                )
    # _fix_id('66340-02A', '66341-01A', '66341', root, repo)
    # _fix_id('66340-02B', '66341-01B', '66341', root, repo)
    identifier = '66550'
    source_identifier = '66560'
    for step in 'ABCDEFGHIJL':
        _fix_id('{}-01{}'.format(source_identifier, step), '{}-01{}'.format(identifier, step), identifier, root, repo)
# ============= EOF =============================================
