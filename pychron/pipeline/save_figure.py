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
from traits.api import HasTraits, Button, Instance
from traitsui.api import View, Item, UItem, VGroup, InstanceEditor, Tabbed
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.pdf.save_pdf_dialog import FigurePDFOptions, PDFLayoutView
from pychron.core.save_model import SaveModel, SaveController
from pychron.core.ui.combobox_editor import ComboboxEditor
from pychron.paths import paths


class SaveFigureModel(SaveModel):
    pdf_options = Instance(FigurePDFOptions)

    def __init__(self, analyses, *args, **kw):
        self.experiment_identifiers = tuple({ai.experiment_identifier for ai in analyses})
        self.root_directory = self.experiment_identifiers[0]

        identifiers = tuple({ai.identifier for ai in analyses})
        self.name = '_'.join(identifiers)

        m = FigurePDFOptions()
        m.load()
        self.pdf_options = m
        super(SaveFigureModel, self).__init__(*args, **kw)

    def dump(self):
        self.pdf_options.dump()


class SaveFigureView(SaveController):
    def _get_root_item(self):
        item = Item('root_directory', label='Directory',
                    editor=ComboboxEditor(name='experiment_identifiers'))
        return item

    def traits_view(self):
        path_group = self._get_path_group()

        options_group = VGroup(UItem('pdf_options',
                                     style='custom',
                                     editor=InstanceEditor(view=PDFLayoutView)),
                               label='Layout')

        v = View(Tabbed(path_group, options_group),
                 buttons=['OK', 'Cancel'],
                 title='Save PDF Dialog',
                 width=700,
                 kind='livemodal')
        return v


if __name__ == '__main__':
    import random

    paths.build('_dev')


    class A(object):
        def __init__(self):
            self.experiment_identifier = random.choice(['Foo', 'Bar', 'Bat'])
            self.identifier = '1000'


    ans = [A() for i in range(5)]
    sfm = SaveFigureModel(ans)
    sfv = SaveFigureView(model=sfm)


    class Demo(HasTraits):
        test = Button

        def traits_view(self):
            return View('test')

        def _test_fired(self):
            sfv.edit_traits()
            # sfv.configure_traits()
            print 'fff', sfm.prepare_path()


    Demo().configure_traits()
# ============= EOF =============================================
