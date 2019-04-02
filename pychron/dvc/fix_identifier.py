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

def _fix_id(src_id, dest_id, identifier, root, repo, new_aliquot=None):
        sp = analysis_path(src_id, repo, root=root)
        dp = analysis_path(dest_id, repo, root=root, mode='w')
        print(sp, dp)
        if not os.path.isfile(sp):
            print('not a file', sp)
            return

        jd = dvc_load(sp)
        jd['identifier'] = identifier
        if new_aliquot:
            jd['aliquot']= new_aliquot

        dvc_dump(jd, dp)

        print('{}>>{}'.format(sp, dp))
        for modifier in ('baselines', 'blanks', 'extraction',
                         'intercepts', 'icfactors', 'peakcenter', '.data'):
            sp = analysis_path(src_id, repo, modifier=modifier, root=root)
            dp = analysis_path(dest_id, repo, modifier=modifier, root=root, mode='w')
            print('{}>>{}'.format(sp,dp))
            if sp and os.path.isfile(sp):
                # shutil.copy(sp, dp)
                shutil.move(sp,dp)


def swap_identifier(a, a_id, b, b_id, c_id, root, repo):
    '''
        a -> c
        replace a with b
        replace b with c
    '''

    _fix_id(a_id, c_id, a, root, repo)
    _fix_id(b_id, a_id, a, root, repo)
    _fix_id(c_id, b_id, b, root, repo)


if __name__ == '__main__':
    root = '/Users/ross/PychronDev/data/.dvc/repositories/'
    repo = 'Henry01104'

    _fix_id('66151-01', '66150-21', '66150', root, repo, new_aliquot=21)
    _fix_id('66151-12', '66150-22', '66150', root, repo, new_aliquot=22)
    _fix_id('66149-20', '66150-23', '66150', root, repo, new_aliquot=23)

    _fix_id('66150-06', '66149-29', '66149', root, repo, new_aliquot=29)


    # repo = 'FCTest'
    #
    # a_id = '26389-03'
    # a = '26389'
    # b_id = '26381-03'
    # b = '26381'
    # c_id = '26389-03X'
    #
    # swap_identifier(a,a_id, b, b_id, c_id, root, repo)
    # repo = 'Saifuddeen01097'
    # fix_identifier('66340', '66431', '/Users/ross/PychronDev/data/.dvc/repositories/',
    #                'Saifuddeen01097',
    #                aliquots=[2],
    #                steps=['A','B']
    #                dest_aliquots=[1]
    #                # aliquots=[1,]#2,3,4,5,6]
    #                )
    # _fix_id('66340-02A', '66341-01A', '66341', root, repo)
    # _fix_id('66340-02B', '66341-01B', '66341', root, repo)
    # identifier = '66550'
    # source_identifier = '66560'
    # for step in 'ABCDEFGHIJL':
    #     _fix_id('{}-01{}'.format(source_identifier, step), '{}-01{}'.format(identifier, step), identifier, root, repo)
# ============= EOF =============================================
