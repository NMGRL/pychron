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
from traits.api import HasTraits, Event
from traitsui.api import View, Item

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.base_editor import BaseTraitsEditor


class BaseUnknownsEditor(BaseTraitsEditor):
    refresh_unknowns_table = Event

    def _grouped_name(self, names, delimiter='-'):
        s = names[0]
        e = names[-1]
        if s != e:
            if all([delimiter in x for x in names]):
                prev = None
                for x in names:
                    nx = x.split(delimiter)
                    h, t = delimiter.join(nx[:-1]), nx[-1]

                    #h, t = x.split(delimiter)
                    if prev and prev != h:
                        #print 'not a group'
                        break
                    prev = h
                else:
                    #print 'is a group'
                    s = names[0]
                    e = names[-1].split(delimiter)[-1]

            s = '{} - {}'.format(s, e)

        return s

#============= EOF =============================================

