# ===============================================================================
# Copyright 2020 ross
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
from traits.api import HasTraits, List, Str, Bool, Instance
from traitsui.api import UItem, HGroup, VGroup, Item, EnumEditor, TabularEditor

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.envisage.browser.adapters import SampleAdapter
from pychron.envisage.browser.record_views import SampleRecordView


class MaterialEditor(HasTraits):
    dvc = Instance("pychron.dvc.dvc.DVC")
    overwrite_material = Bool
    material = Str
    grainsize = Str

    materials = List

    samples = List
    selected = Instance(SampleRecordView)

    def activate(self, irradpos):
        dvc = self.dvc
        with dvc.session_ctx():
            # get all the available sample records for this sample 'name'
            self.samples = [
                SampleRecordView(si) for si in dvc.get_samples(name=irradpos.sample)
            ]
            self.materials = dvc.get_material_names()

    def save(self, irrad, level, pos):
        dvc = self.dvc
        with dvc.session_ctx():
            dbip = dvc.get_irradiation_position(irrad, level, pos.hole)
            if self.selected:
                dbsam = dvc.get_sample_id(self.selected.id)
            else:
                if self.overwrite_material:
                    dbsam = dbip.sample
                    dbmat = dvc.add_material(self.material, self.grainsize)
                    dbsam.material = dbmat
                else:
                    dbsam = dvc.add_sample(
                        pos.sample,
                        pos.project,
                        pos.principal_investigator,
                        self.material,
                        grainsize=self.grainsize,
                    )
            dbip.sample = dbsam
            dvc.commit()

    def traits_view(self):
        v = okcancel_view(
            VGroup(
                Item("overwrite_material", label="Overwrite"),
                HGroup(
                    UItem("material", editor=EnumEditor(name="materials")),
                    Item("grainsize"),
                ),
                UItem(
                    "samples",
                    editor=TabularEditor(adapter=SampleAdapter(), selected="selected"),
                ),
            ),
            title="Edit Material",
        )
        return v


# ============= EOF =============================================
