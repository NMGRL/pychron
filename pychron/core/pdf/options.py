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
from traits.api import HasTraits, Str, Bool, Color, Enum, Button, Float, TraitError
from traitsui.api import View, Item, UItem, HGroup, Group

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.pane_helpers import icon_button_editor


class BasePDFOptions(HasTraits):
    orientation = Enum('landscape', 'portrait')
    left_margin = Float(1.5)
    right_margin = Float(1)
    top_margin = Float(1)
    bottom_margin = Float(1)

    def dump_yaml(self):
        d = dict(orientation=self.orientation,
                 left_margin=self.left_margin,
                 right_margin=self.right_margin,
                 top_margin=self.top_margin,
                 bottom_margin=self.bottom_margin)

        return d

    def load_yaml(self, d):
        for k, v in d.iteritems():
            try:
                setattr(self, k, v)
            except TraitError:
                pass


class PDFTableOptions(BasePDFOptions):
    title = Str
    auto_title = Bool
    use_alternating_background = Bool
    alternating_background = Color
    show_page_numbers = Bool
    default_row_height = Float(0.22)
    default_header_height = Float(0.22)
    options_button = Button
    nsigma = Enum(1, 2, 3)

    def _default_nsigma(self):
        return 2

    def load_yaml(self, d):
        super(PDFTableOptions, self).load_yaml(d)

        ab = d.get('alternating_background', False)
        self.set_alternating_background(ab)
        self.nsigma = d.get('nsigma', 2)

    def dump_yaml(self):
        """
            return an object to be dumped in a yaml file
        """
        d = super(PDFTableOptions, self).dump_yaml()
        d.update(dict(title=str(self.title),
                      auto_title=self.auto_title,
                      use_alternating_background=self.use_alternating_background,
                      alternating_background=self.get_alternating_background(),
                      show_page_numbers=self.show_page_numbers,
                      nsigma=self.nsigma))

        return d

    def set_alternating_background(self, t):
        self.alternating_background = tuple(map(lambda x: int(x * 255), t))

    def get_alternating_background(self):
        t = self.alternating_background.toTuple()[:3]
        return map(lambda x: x / 255., t)

    def _options_button_fired(self):
        self.edit_traits(view='advanced_view', kind='livemodal')

    def traits_view(self):
        v = View(HGroup(Item('auto_title'),
                        UItem('title', enabled_when='not auto_title'),
                        icon_button_editor('options_button', 'cog')))
        return v

    def advanced_view(self):
        table_grp = Group(Item('use_alternating_background'),
                          Item('alternating_background'),
                          label='Table')

        layout_grp = Group(Item('orientation'),
                           Item('left_margin'),
                           Item('right_margin'),
                           Item('top_margin'),
                           Item('bottom_margin'),
                           label='layout')
        data_grp = Group(Item('nsigma'))
        v = View(
            layout_grp,
            table_grp,
            data_grp,
            title='PDF Options',
            buttons=['OK', 'Cancel', 'Revert'])
        return v
        #============= EOF =============================================