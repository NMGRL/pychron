# ===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Property, Enum, Str, on_trait_change, List
from traitsui.api import View, Item, InstanceEditor, Handler, ListStrEditor, EnumEditor, VGroup, UItem, HGroup
# ============= standard library imports ========================
from pychron.core.helpers.filetools import add_extension, list_directory2
import cPickle as pickle
import os
# ============= local library imports  ==========================
from pychron.lasers.pattern.patternable import Patternable
from pychron.saveable import Saveable, SaveableButtons
from pychron.paths import paths
from pychron.stage.stage_manager import get_stage_map_names


class PatternMakerHandler(Handler):
    def object_pattern_name_changed(self, info):
        info.ui.title = 'Pattern Editor - {}'.format(info.object.pattern_name)

    def save(self, info):
        info.object.save()

    def save_as(self, info):
        info.object.save_as()


class PatternMakerView(Saveable, Patternable):
    kind = Property(Enum('Polygon',
                         'Linear',
                         'Arc',
                         'LineSpiral',
                         'SquareSpiral',
                         'Random',
                         'CircularContour', 'Trough',
                         'Rubberband', 'RasterRubberband',
                         'Seek', 'DragonFly'),
                    depends_on='_kind')
    _kind = Str('Polygon')

    tray_name = Str
    trays = List
    new_name = Property(depends_on='tray_name')

    def __init__(self, *args, **kw):
        super(PatternMakerView, self).__init__(*args, **kw)
        self._load_pattern_names()

    def load_pattern(self, path=None):
        if path is None:
            return

        # path = self.open_file_dialog(default_directory=paths.pattern_dir)
        if not os.path.isfile(path):
            path = os.path.join(paths.pattern_dir, path)

        if path and os.path.isfile(path):
            with open(path, 'r') as rfile:
                pattern = self._load_pattern(rfile, path)
                if pattern:
                    self._kind = pattern.__class__.__name__.replace('Pattern', '')
                    return True

            self.warning_dialog('{} is not a valid pattern file'.format(path))

    @on_trait_change('pattern:+')
    def pattern_dirty(self):
        if self.pattern.path:
            self.save_enabled = True

    def save(self):
        if self.pattern.path:
            self._save(self.pattern.path)
            self.save_enabled = False

    def save_as(self):
        self.trays = get_stage_map_names()

        v = self._save_as_view()
        while 1:
            info = self.edit_traits(v)
            if info.result:
                if not self.tray_name:
                    self.warning_dialog('Please select a tray name when trying to save a new pattern')
                else:
                    n = self._generate_name()
                    self._save(os.path.join(paths.pattern_dir, n))
                    self._load_pattern_names()
                    break
            else:
                break

    def _save(self, path):
        path = add_extension(path, '.lp')
        self.pattern.path = path
        with open(path, 'wb') as f:
            pickle.dump(self.pattern, f)
        self.info('pattern saved as {}'.format(path))

    def _generate_name(self):
        return '{}-{}'.format(self.pattern.generate_name(), self.tray_name).lower()

    def _selected_pattern_name_changed(self, new):
        print new
        if not new:
            return

        p = add_extension(new, '.lp')
        if self.save_enabled:
            if self.confirmation_dialog('You have unsaved changes. Are you sure you want to continue?'):
                self.load_pattern(p)
        else:
            self.load_pattern(p)

    def _load_pattern_names(self):
        self.patterns = list_directory2(paths.pattern_dir, extension='.lp', remove_extension=True)

    def _save_as_view(self):
        v = View(Item('tray_name', editor=EnumEditor(name='trays')),
                 Item('new_name', style='readonly'),
                 buttons=['OK', 'Cancel'],
                 kind='livemodal',
                 resizable=True,
                 width=300,
                 title='Pattern Save As')
        return v

    def traits_view(self):
        bgrp = VGroup(UItem('patterns',
                            editor=ListStrEditor(selected='selected_pattern_name')))
        ngrp = VGroup(Item('kind', show_label=False),
                      Item('pattern',
                           style='custom',
                           editor=InstanceEditor(view='maker_view'),
                           show_label=False))

        v = View(HGroup(bgrp, ngrp),
                 handler=PatternMakerHandler(),
                 buttons=SaveableButtons,
                 height=425,
                 title='Pattern Editor',
                 resizable=True)
        return v

    # ===============================================================================
    # property get/set
    # ===============================================================================
    def _get_kind(self):
        return self._kind

    def _set_kind(self, v):
        self._kind = v

        pat = self.pattern_factory(v)
        if pat:
            self.pattern = pat

    def _get_new_name(self):
        return self._generate_name()
    # ===============================================================================
    # factories
    # ===============================================================================
    def pattern_factory(self, kind):
        pattern = None
        name = '{}Pattern'.format(kind)
        for pkg in ('pychron.lasers.pattern.patterns',
                    'pychron.lasers.pattern.seek_pattern',
                    'pychron.lasers.pattern.degas_pattern'):
            try:
                factory = __import__(pkg, fromlist=[name])
                pattern = getattr(factory, name)()
                break
            except (ImportError, AttributeError), e:
                pass

                #
                # try:
                #     factory = __import__('pychron.lasers.pattern.seek_pattern',
                #                          fromlist=[name])
                #     pattern = getattr(factory, name)()
                # except ImportError, e:
                #     print e

        if pattern:
            pattern.replot()
            pattern.calculate_transit_time()
            return pattern

    # ===============================================================================
    # defaults
    # ===============================================================================
    def _pattern_default(self):
        p = self.pattern_factory(self.kind)
        return p


if __name__ == '__main__':
    paths.build('_dev')
    pm = PatternMakerView()
    pm.trays = ['a','b','c']
    # pm.load_pattern()
    pm.configure_traits()
# ============= EOF =============================================
