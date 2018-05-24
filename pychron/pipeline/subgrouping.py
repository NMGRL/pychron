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


import hashlib
from itertools import groupby

from pychron.processing.analyses.analysis_group import InterpretedAgeGroup


def set_subgrouping_error(tag, selected, items):

    ss = []
    for s in selected:
        if s.subgroup:
            s.subgroup['error_kind'] = tag
            ss.append(s.subgroup['name'])

    if ss:
        # ensure all items in the subgroup get updated
        for i in items:
            if i.subgroup and i.subgroup['name'] in ss:
                i.subgroup['error_kind'] = tag


def apply_subgrouping(kind, error_kind, selected, items=None, gid=None):
    if len(selected) == 1:
        return

    if items is None and gid is None:
        raise ValueError('must set items or gid')

    if items:
        gs = {r.subgroup['name'] for r in items}
        gs = [int(gi) for gi in gs if gi]
        gid = max(gs) + 1 if gs else 0

    sha = hashlib.sha1()
    for s in selected:
        sha.update(s.uuid.encode('utf-8'))

    sha_id = sha.hexdigest()
    # sg = {'name':'{}:{}_{}'.format(sha_id, tag, gid),'error_kind': }
    sg = {'name': '{:02n}'.format(gid), 'kind': kind, 'error_kind': error_kind, 'sha_id': sha_id}
    for s in selected:
        s.subgroup = sg

    if items:
        compress_groups(items)


def compress_groups(items):
    # compress groups
    # key = lambda x: '_'.join(x.subgroup.split(':')[-1].split('_')[:-1]) if x.subgroup else ''

    def key(x):
        return x.subgroup['name'] if x.subgroup else ''

    # gkey = attrgetter('group_id')
    cnt = 0
    for kind, ans in groupby(sorted(items, key=key), key=key):
        if kind:
            ans = list(ans)
            valid_ais = [a for a in ans if not a.is_omitted()]
            v = '{:02n}'.format(cnt) if len(valid_ais) > 1 else ''

            for a in ans:
                a.subgroup['name'] = v

            cnt += 1
            # for i, (_, ais) in enumerate(groupby(ans, key=key)):
            #     ais = list(ais)
            #     valid_ais = [a for a in ais if not a.is_omitted()]
            #     v = i if len(valid_ais) > 1 else ''
            #
            #     print('asfdasfdasd', v, i)
            #     for a in ais:
            #         a.subgroup['name'] = v

        else:
            for a in ans:
                a.subgroup = None

    # gs = {r.subgroup for r in items}
    # if len(gs) == 1:
    #     for a in items:
    #         a.subgroup = ''


def subgrouping_key(x):
    return x.subgroup['name'] if x.subgroup else ''


def make_interpreted_age_subgroups(ans):

    ias = []

    for subgroup, items in groupby(ans, key=subgrouping_key):
        items = list(items)
        if subgroup:
            item = items[0]
            kind = item.subgroup['kind']
            error_kind = item.subgroup['error_kind']
        # else:
        #     kind = 'weighted_mean'
        #     error_kind = MSEM

            ag = InterpretedAgeGroup(analyses=list(items),
                                     preferred_age_kind=kind,
                                     preferred_age_error_kind=error_kind)
            ag.label_name = '{:02n}{}'.format(ag.aliquot, kind[:2])
            ag.record_id = '{:02n}{}'.format(ag.aliquot, kind[:2])

            ias.append(ag)
        else:
            ias.extend(items)

    return ias

# ============= EOF =============================================
