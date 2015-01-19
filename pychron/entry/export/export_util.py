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
from traits.api import HasTraits, Button
from traitsui.api import View, Item
# ============= standard library imports ========================
#============= local library imports  ==========================
EXP_DICT = {'MassSpec': ('pychron.entry.export.mass_spec_irradiation_exporter', 'MassSpecIrradiationExporter'),
            'XML': ('pychron.entry.export.xml_irradiation_exporter', 'XMLIrradiationExporter'),
            'YAML': ('pychron.entry.export.yaml_irradiation_exporter', 'YAMLIrradiationExporter'),
            'XLS': ('pychron.entry.export.xls_irradiation_exporter', 'XLSIrradiationExporter')}


def do_export(source, export_type, destination, irradiations):
    modpath, klass = EXP_DICT[export_type]
    mod = __import__(modpath, fromlist=[klass])
    ex = getattr(mod, klass)(destination_spec=destination, source=source)
    ex.do_export(irradiations)

#============= EOF =============================================



