#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================

#============= standard library imports ========================
#============= local library imports  ==========================
from collections import deque


def bfs(G, s, value, attr='name'):
    P, Q = {s: None}, deque([s])
    while Q:
        u = Q.popleft()
        if not u:
            continue

        print u.name, value, getattr(u, attr) == value
        if getattr(u, attr) == value:
            return u

        for v in G[u]:
            if v in P:
                continue
            P[v] = u
            Q.append(v)


def bft(G, s, traverse_all=False):
    P, Q = {s: None}, deque([s])
    while Q:
        u = Q.popleft()
        if not u:
            continue

        if not traverse_all:
            if u.state == 'closed':
                continue

        for v in G[u]:
            if v in P:
                continue
            P[v] = u
            Q.append(v)

    return P
#============= EOF =============================================
