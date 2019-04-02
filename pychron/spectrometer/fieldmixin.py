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
from __future__ import absolute_import

from traits.api import Instance, HasTraits


class FieldMixin(HasTraits):
    field_table = Instance('pychron.spectrometer.field_table.FieldTable', ())

    def field_table_setup(self):
        if self.spectrometer:
            molweights = self.spectrometer.molecular_weights
            name = self.spectrometer.name
        else:
            from pychron.spectrometer.molecular_weights import MOLECULAR_WEIGHTS as molweights

            name = ''

        self.field_table.initialize(molweights)
        self.field_table.spectrometer_name = name.lower()

    def reload_field_table(self, *args, **kw):
        self.field_table.load_table(*args, **kw)

    def set_mftable(self, name):
        self.field_table.set_path_name(name)

    def update_field_table(self, *args, **kw):
        self.field_table.update_field_table(*args, **kw)
# ============= EOF =============================================
