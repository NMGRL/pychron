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
from pyface.constant import OK
from pyface.file_dialog import FileDialog
from traits.api import HasTraits, Str, Button, Instance, Bool
from traitsui.api import View, Item, Controller, UItem, VGroup, HGroup, spring, InstanceEditor, Tabbed
# ============= standard library imports ========================
import os
# ============= local library imports  ==========================
from pychron.core.helpers.filetools import unique_path2, add_extension
from pychron.core.pdf.save_pdf_dialog import FigurePDFOptions, PDFLayoutView
from pychron.core.ui.combobox_editor import ComboboxEditor
from pychron.paths import paths


class SaveFigureModel(HasTraits):
    root_directory = Str
    name = Str
    path = Str
    use_manual_path = Bool(False)
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

    def prepare_path(self, make=False):
        if self.use_manual_path:
            return self.path
        else:
            return self._prepare_path(make=make)

    def _prepare_path(self, make=False):
        root = os.path.join(paths.figure_dir, self.root_directory)
        if make and not os.path.isdir(root):
            os.mkdir(root)

        path, cnt = unique_path2(root, self.name, extension='.pdf')
        return path


class SaveFigureView(Controller):
    use_finder_button = Button('Use Finder')

    def closed(self, info, is_ok):
        if is_ok:
            self.model.dump()

    def _use_finder_button_fired(self):
        dlg = FileDialog(action='save as')
        if dlg.open() == OK:
            self.model.use_manual_path = True
            self.model.path = add_extension(dlg.path, '.pdf')

    def object_name_changed(self, info):
        self._set_path()

    def object_root_directory_changed(self, info):
        self._set_path()

    def _set_path(self):
        self.model.use_manual_path = False
        path = self.model.prepare_path()
        self.model.path = path

    def traits_view(self):
        path_group = VGroup(Item('root_directory', label='Directory',
                                 editor=ComboboxEditor(name='experiment_identifiers')),
                            Item('name'),
                            HGroup(UItem('controller.use_finder_button'), spring),
                            Item('path', style='readonly'),
                            label='File')

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
