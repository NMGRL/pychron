import hashlib
from itertools import groupby
from operator import attrgetter

__author__ = 'ross'


def apply_subgrouping(tag, selected, items=None, gid=None):
    if len(selected) == 1:
        return

    if items is None and gid is None:
        raise ValueError('must set items or gid')

    if items:
        gs = {r.subgroup for r in items}
        gs = [int(gi.split('_')[-1]) for gi in gs if gi]
        gid = max(gs) + 1 if gs else 0

    sha = hashlib.sha1()
    for s in selected:
        sha.update(s.uuid.encode('utf-8'))

    sha_id = sha.hexdigest()
    for s in selected:
        s.subgroup = '{}:{}_{}'.format(sha_id, tag, gid)

    if items:
        compress_groups(items)


def compress_groups(items):
    # compress groups
    key = lambda x: '_'.join(x.subgroup.split(':')[-1].split('_')[:-1]) if x.subgroup else ''
    for kind, ans in groupby(sorted(items, key=key), key=key):
        if kind:
            for i, (_, ais) in enumerate(groupby(ans, key=attrgetter('subgroup'))):
                ais = list(ais)
                valid_ais = [a for a in ais if not a.is_omitted()]
                v = '{}_{}'.format(kind, i) if len(valid_ais) > 1 else ''

                for a in ais:
                    a.subgroup = v

        else:
            for a in ans:
                a.subgroup = ''

    gs = {r.subgroup for r in items}
    if len(gs) == 1:
        for a in items:
            a.subgroup = ''
