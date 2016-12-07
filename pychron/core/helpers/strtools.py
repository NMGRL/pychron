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

def camel_case(name, delimiters=None):
    if delimiters is None:
        delimiters = ('_', '/', ' ')

    name = '{}{}'.format(name[0].upper(), name[1:])
    for d in delimiters:
        if d in name:
            name = ''.join(a.title() for a in name.split(d))

    return name


def to_list(a, delimiter=',', mapping=None):
    l = a.split(delimiter)
    if mapping:
        l = map(mapping, l)
    return l


def to_bool(a):
    """
        a: a str or bool object

        if a is string
            'true', 't', 'yes', 'y', '1', 'ok' ==> True
            'false', 'f', 'no', 'n', '0' ==> False
    """

    if isinstance(a, bool):
        return a
    elif a is None:
        return False
    elif isinstance(a, (int, float)):
        return bool(a)

    tks = ['true', 't', 'yes', 'y', '1', 'ok']
    fks = ['false', 'f', 'no', 'n', '0']

    # if a is not None:
    #     a = str(a).strip().lower()

    a = str(a).strip().lower()
    if a in tks:
        return True
    elif a in fks:
        return False
# ============= EOF =============================================
