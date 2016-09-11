# ===============================================================================
# Copyright 2016 ross
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

from traits.trait_types import Event

from pychron.core.helpers.filetools import list_directory2, list_directory
from pychron.experiment.utilities.position_regex import SLICE_REGEX, SSLICE_REGEX, PSLICE_REGEX, CSLICE_REGEX, \
    TRANSECT_REGEX
from pychron.paths import paths
from pychron.pychron_constants import LINE_STR, NULL_STR


class EditEvent(Event):
    pass


class UpdateSelectedCTX(object):
    _factory = None

    def __init__(self, factory):
        self._factory = factory

    def __enter__(self):
        self._factory.set_labnumber = False
        self._factory.set_position = False

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._factory.set_labnumber = True
        self._factory.set_position = True


def EKlass(klass):
    return klass(enter_set=True, auto_set=False)


def increment_value(m, increment=1):
    s = ','
    if s not in m:
        m = (m,)
        s = ''
    else:
        m = m.split(s)

    ms = []
    for mi in m:
        try:
            ms.append(str(int(mi) + increment))
        except ValueError:
            return s.join(m)

    return s.join(ms)


def increment_position(pos):
    for regex, sfunc, ifunc, _ in (SLICE_REGEX, SSLICE_REGEX,
                                   PSLICE_REGEX, CSLICE_REGEX, TRANSECT_REGEX):
        if regex.match(pos):
            return ifunc(pos)
    else:
        m = map(int, pos.split(','))
        ms = []
        offset = max(m) - min(m)
        inc = 1
        for i, mi in enumerate(m):
            try:
                inc = m[i + 1] - mi
            except IndexError:
                pass
            ms.append(mi + offset + inc)
        return ','.join(map(str, ms))


def generate_positions(pos):
    for regex, func, ifunc, _ in (SLICE_REGEX, SSLICE_REGEX,
                                  PSLICE_REGEX, CSLICE_REGEX, TRANSECT_REGEX):
        if regex.match(pos):
            return func(pos)
    else:
        return [pos]


def get_run_blocks():
    p = paths.run_block_dir
    blocks = list_directory2(p, '.txt', remove_extension=True)
    return ['RunBlock', LINE_STR] + blocks


def get_comment_templates():
    p = paths.comment_templates
    templates = list_directory(p)
    return templates


def remove_file_extension(name, ext='.py'):
    if not name:
        return name

    if name is NULL_STR:
        return NULL_STR

    if name.endswith('.py'):
        name = name[:-3]

    return name
# ============= EOF =============================================
