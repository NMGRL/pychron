# ===============================================================================
# Copyright 2016 Jake Ross
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
'''
Adapted from
http://norvig.com/spell-correct.html
'''

alphabet = 'abcdefghijklmnopqrstuvwxyz'


def edits1(word):
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes = [a + b[1:] for a, b in splits if b]
    transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b) > 1]
    replaces = [a + c + b[1:] for a, b in splits for c in alphabet if b]
    inserts = [a + c + b for a, b in splits for c in alphabet]
    return set(deletes + transposes + replaces + inserts)


def edits2(word):
    return set(e2 for e1 in edits1(word) for e2 in edits1(e1))


def known_edits2(word, possibles):
    return set(e2 for e1 in edits1(word) for e2 in edits1(e1) if e2 in possibles)


def known(words, possibles):
    return set(w for w in words if w in possibles)


def correct(word, possibles):
    lpossibles = [p.lower() for p in possibles]

    candidates = known([word], lpossibles) or \
                 known(edits1(word), lpossibles) or \
                 known_edits2(word, lpossibles) or [word]

    result = list(candidates)[0]

    if result in lpossibles:
        idx = lpossibles.index(result)
        result = possibles[idx]

    return result
    # print candidates
    # return max(candidates, key=possibles.get)

# ============= EOF =============================================
