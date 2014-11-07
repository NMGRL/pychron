# ===============================================================================
# Copyright 2014 Jake Ross
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
from datetime import datetime
import os
import time
import weakref
from traits.api import HasTraits, Button, Str, Int, Bool, Any, List, Property, Event, cached_property
from traitsui.api import View, Item, UItem, HGroup, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
from pychron.core.helpers.filetools import created_datetime, modified_datetime
from pychron.paths import paths


class FilePathAdapter(TabularAdapter):
    columns = [('Name', 'name'),
               ('Create', 'create_date'),
               ('Modified', 'modified_date')]

    name_text = Property
    font = '10'

    def _get_name_text(self):
        return os.path.relpath(self.item.path, paths.labbook_dir)


class FilePath(HasTraits):
    name = Str
    root = Any
    root_path = Str

    @property
    def path(self):
        '''
            recursively assemble the path to this resourse
        '''
        if self.root:
            return os.path.join(self.root.path, self.name)
        elif self.root_path:
            return self.root_path
            # return '{}/{}'.format(self.root.path, self.name)
        else:
            return self.name



class Hierarchy(FilePath):
    children = List

    chronology = Property(List)  # Property(depends_on='refresh_needed, children')
    # refresh_needed=Event

    # def reset_chronology(self):
    # self.refresh_needed=True
    def _get_chronology(self):
        files = self._flatten()
        return sorted(files, key=lambda x: x.create_date, reverse=True)

    def _flatten(self):
        for ci in self.children:
            if isinstance(ci, Hierarchy):
                for x in ci._flatten():
                    yield x
            else:
                yield ci

    def _children_changed(self):
        for ci in self.children:
            ci.root = weakref.ref(self)()
            ci.create_date = created_datetime(ci.path)
            ci.modified_date = modified_datetime(ci.path)

    def pwalk(self):
        for ci in self.children:
            print self.name, ci.path, ci.__class__.__name__
            if isinstance(ci, Hierarchy):
                ci.pwalk()

    # @property
    # def high_post(self):
    #     c=self._get_chronology()
    #     return c[0]
    #
    # @property
    # def low_post(self):
    #     c=self._get_chronology()
    #     return c[-1]
# ============= EOF =============================================



