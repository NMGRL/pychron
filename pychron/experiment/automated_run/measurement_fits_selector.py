#===============================================================================
# Copyright 2014 Jake Ross
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
import ast

from pychron.core.helpers.filetools import add_extension
from pychron.core.ui import set_qt

set_qt()

#============= enthought library imports =======================
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn

from traits.api import Str
from traitsui.api import View, HGroup, UItem, VGroup, EnumEditor
from traitsui.handler import Controller

#============= standard library imports ========================
import os
import yaml
#============= local library imports  ==========================
from pychron.paths import paths, build_directories
from pychron.core.ui.table_editor import myTableEditor
from pychron.processing.fits.filter_fit_selector import FilterFitSelector, FilterFit


class MeasurementFit(FilterFit):
    pass


ATTRS = ['fit', 'error_type', 'name', 'filter_outliers', 'filter_iterations', 'filter_std_devs']


class MeasurementFitsSelector(FilterFitSelector):
    fit_klass = MeasurementFit
    name = Str

    def open(self, script_path):
        dfp = self._extract_default_fits_file(script_path)
        if dfp:
            self.load(os.path.join(paths.fits_dir, add_extension(dfp, '.yaml')))

    def _extract_default_fits_file(self, path):
        with open(path, 'r') as fp:
            m = ast.parse(fp.read())
            docstr = ast.get_docstring(m)
            yd = yaml.load(docstr)
            return yd.get('default_fits')

    def save(self):
        ys = []
        for fi in self.fits:
            d = {ai: getattr(fi, ai) for ai in ATTRS}
            ys.append(d)

        p = os.path.join(paths.fits_dir, '{}.yaml'.format(self.name))
        with open(p, 'w') as fp:
            yaml.dump(ys, fp, default_flow_style=False)

    def load(self, p):
        with open(p, 'r') as fp:
            yd = yaml.load(fp)
            fits = self._load_fits(yd['signal'])
            fits.extend(self._load_fits(yd['baseline']))
            self.fits = fits

        h, _ = os.path.splitext(os.path.basename(p))
        self.name = h

    def _load_fits(self, fs):
        fits = []
        for fi in fs:
            d = {ai: fi[ai] for ai in ATTRS}
            f = MeasurementFit(**d)
            fits.append(f)
        return fits


class MeasurementFitsSelectorView(Controller):
    def closed(self, info, is_ok):
        if is_ok:
            self.model.save()

    def _get_toggle_group(self):
        g = HGroup(
            UItem('filter_all_button'), )
        return g

    def _get_auto_group(self):
        return HGroup(UItem('global_fit', editor=EnumEditor(name='fit_types')),
                      UItem('global_error_type', editor=EnumEditor(name='error_types')))

    def _get_fit_group(self):
        cols = [ObjectColumn(name='name', editable=False),
                ObjectColumn(name='fit',
                             editor=EnumEditor(name='fit_types'),
                             width=75),
                ObjectColumn(name='error_type',
                             editor=EnumEditor(name='error_types'),
                             label='Error',
                             width=75),
                CheckboxColumn(name='filter_outliers', label='Out.'),
                ObjectColumn(name='filter_iterations', label='Iter.'),
                ObjectColumn(name='filter_std_devs', label='SD')]

        editor = myTableEditor(columns=cols,
                               selected='selected',
                               selection_mode='rows',
                               sortable=False,
                               clear_selection_on_dclicked=True,
                               on_command_key=self._update_command_key,
                               cell_bg_color='red',
                               cell_font='modern 10')
        grp = UItem('fits',
                    style='custom',
                    editor=editor)
        return grp

    def traits_view(self):
        v = View(VGroup(UItem('name'),
                        self._get_toggle_group(),
                        self._get_auto_group(),
                        self._get_fit_group()),
                 title='Edit Default Fits',
                 buttons=['OK', 'Cancel'],
                 resizable=True)
        return v


if __name__ == '__main__':
    build_directories(paths)
    m = MeasurementFitsSelector()

    # keys = ['Ar40', 'Ar39']
    # detectors=['H1','AX']
    # fits = [('linear', 'SEM', {}),
    #         ('linear', 'SEM', {})]

    t = os.path.join(paths.fits_dir, 'test.yaml')
    m.load(t)
    a = MeasurementFitsSelectorView(model=m)
    a.configure_traits()



#============= EOF =============================================

