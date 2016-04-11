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
from itertools import groupby

from enable.markers import marker_names
from traits.api import HasTraits, Str, Int, Bool, Float, Property, Enum, List, Range, \
    Color, Button
from traitsui.api import View, Item, HGroup, VGroup, EnumEditor, Spring, Group, \
    spring, UItem, ListEditor, InstanceEditor
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.handler import Controller
from traitsui.table_column import ObjectColumn
# ============= standard library imports ========================
import os
import yaml
# ============= local library imports  ==========================
from pychron.core.helpers.color_generators import colornames
from pychron.core.ui.table_editor import myTableEditor
from pychron.options.aux_plot import AuxPlot
from pychron.pychron_constants import NULL_STR, ERROR_TYPES, FONTS, SIZES, ALPHAS


def _table_column(klass, *args, **kw):
    kw['text_font'] = 'arial 10'
    return klass(*args, **kw)


def object_column(*args, **kw):
    return _table_column(ObjectColumn, *args, **kw)


def checkbox_column(*args, **kw):
    return _table_column(CheckboxColumn, *args, **kw)


class SubOptions(Controller):
    # traits_view = View(Item('index_attr', label='Foo'))
    def _make_view(self, *args, **kw):
        if 'scrollable' not in kw:
            kw['scrollable'] = True
        return View(*args, **kw)


class GroupSubOptions(SubOptions):
    def traits_view(self):
        g = UItem('groups',
                  style='custom',
                  editor=ListEditor(mutable=False,
                                    style='custom',
                                    editor=InstanceEditor())),
        # buttons=['OK', 'Cancel', 'Revert'],
        # kind='livemodal', resizable=True,
        # height=700,
        # title='Group Attributes')
        return self._make_view(g)


class AppearanceSubOptions(SubOptions):
    def _get_xfont_group(self):
        v = VGroup(self._create_axis_group('x', 'title'),
                   self._create_axis_group('x', 'tick'),
                   show_border=True, label='X Axis')
        return v

    def _get_yfont_group(self):
        v = VGroup(self._create_axis_group('y', 'title'),
                   self._create_axis_group('y', 'tick'),
                   show_border=True, label='Y Axis')
        return v

    def _create_axis_group(self, axis, name):
        hg = HGroup(
            Item('{}{}_fontname'.format(axis, name), label=name.capitalize()),
            Item('{}{}_fontsize'.format(axis, name), show_label=False))
        return hg

    def _get_padding_group(self):
        return VGroup(HGroup(Spring(springy=False, width=100),
                             Item('padding_top', label='Top'),
                             spring, ),
                      HGroup(Item('padding_left', label='Left'),
                             Item('padding_right', label='Right')),
                      HGroup(Spring(springy=False, width=100), Item('padding_bottom', label='Bottom'),
                             spring),
                      Item('plot_spacing', label='Spacing', tooltip='Space between plots in pixels'),
                      enabled_when='not formatting_options',
                      label='Padding/Spacing', show_border=True)

    def _get_bg_group(self):
        grp = Group(Item('bgcolor', label='Figure'),
                    Item('plot_bgcolor', label='Plot'),
                    show_border=True,
                    enabled_when='not formatting_options',
                    label='Background')
        return grp

    def _get_grid_group(self):
        grid_grp = VGroup(Item('use_xgrid',
                               label='XGrid Visible'),
                          Item('use_ygrid', label='YGrid Visible'),
                          show_border=True,
                          label='Grid')
        return grid_grp

    def traits_view(self):
        fgrp = VGroup(UItem('fontname'),
                      HGroup(self._get_xfont_group(),
                             self._get_yfont_group()),
                      label='Fonts', show_border=True)

        g = VGroup(self._get_bg_group(),
                   self._get_padding_group(),
                   self._get_grid_group())

        return self._make_view(VGroup(g, fgrp))


class MainOptions(SubOptions):
    def _get_columns(self):
        cols = [checkbox_column(name='plot_enabled', label='Use'),
                object_column(name='name',
                              width=130,
                              editor=EnumEditor(name='names')),
                object_column(name='scale'),
                object_column(name='height',
                              format_func=lambda x: str(x) if x else ''),
                checkbox_column(name='show_labels', label='Labels'),
                checkbox_column(name='x_error', label='X Err.'),
                checkbox_column(name='y_error', label='Y Err.'),
                checkbox_column(name='ytick_visible', label='Y Tick'),
                checkbox_column(name='ytitle_visible', label='Y Title'),
                checkbox_column(name='has_filter', label='Filter', editable=False)
                # object_column(name='filter_str', label='Filter')
                ]

        return cols

    def _get_edit_view(self):
        v = View(VGroup(HGroup(Item('name', editor=EnumEditor(name='names')),
                               Item('scale', editor=EnumEditor(values=['linear', 'log']))),
                        Item('height'),
                        HGroup(UItem('marker', editor=EnumEditor(values=marker_names)),
                               Item('marker_size', label='Size'),
                               show_border=True, label='Marker'),
                        HGroup(Item('ymin', label='Min'),
                               Item('ymax', label='Max'),
                               show_border=True,
                               label='Y Limits'),
                        show_border=True))
        return v

    def traits_view(self):
        aux_plots_grp = Item('aux_plots',
                             style='custom',
                             width=525,
                             show_label=False,
                             editor=myTableEditor(columns=self._get_columns(),
                                                  sortable=False,
                                                  deletable=False,
                                                  clear_selection_on_dclicked=True,
                                                  # edit_on_first_click=False,
                                                  # on_select=lambda *args: setattr(self, 'selected', True),
                                                  # selected='selected',
                                                  edit_view=self._get_edit_view(),
                                                  reorderable=False))
        return self._make_view(aux_plots_grp)


# ===============================================================
# ===============================================================

class BaseOptions(HasTraits):
    fontname = Enum(*FONTS)
    _main_options_klass = MainOptions

    def to_dict(self):
        keys = [trait for trait in self.traits() if
                not trait.startswith('trait') and not trait.endswith('button') and self.to_dict_test(trait)]

        return {key: self.formatted_attr(key) for key in keys}

    def formatted_attr(self, key):
        obj = getattr(self, key)
        if 'color' in key:
            obj = obj.toTuple()
        return obj

    def to_dict_test(self, k):
        return True

    def load_factory_defaults(self, path):
        if not os.path.isfile(path):
            yd = yaml.load(path)
        else:
            with open(path, 'r') as rfile:
                yd = yaml.load(rfile)

        self._load_factory_defaults(yd)

    def initialize(self):
        pass

    def set_names(self, names):
        pass

    def set_detectors(self, dets):
        pass

    def _fontname_changed(self):
        print 'setting font name', self.fontname
        self._set_fonts(self.fontname)
        for attr in self.traits():
            if attr.endswith('_fontname'):
                setattr(self, attr, self.fontname)

    def _set_fonts(self, name):
        pass

    def get_subview(self, name):
        name = name.lower()
        # if hasattr(self, name):
        #     return getattr(self, name)
        # else:
        if name == 'main':
            try:
                klass = self._get_subview(name)
            except KeyError:
                klass = self._main_options_klass
        else:
            klass = self._get_subview(name)

        obj = klass(model=self)
        # obj = self._views[name](model=self)
        return obj

    def _get_subview(self, name):
        raise NotImplementedError

    def _load_factory_defaults(self, yd):
        for k, v in yd.items():
            if hasattr(self, k):
                setattr(self, k, v)


class FigureOptions(BaseOptions):
    bgcolor = Color
    plot_bgcolor = Color
    plot_spacing = Range(0, 50)
    padding_left = Int(100)
    padding_right = Int(100)
    padding_top = Int(100)
    padding_bottom = Int(100)
    auto_generate_title = Bool
    include_legend = Bool(False)
    include_sample_in_legend = Bool
    legend_location = Enum('Upper Right', 'Upper Left', 'Lower Left', 'Lower Right')
    title = Str
    title_formatter = Str
    title_attribute_keys = List
    title_delimiter = Str(',')
    title_leading_text = Str
    title_trailing_text = Str
    edit_title_format_button = Button

    use_xgrid = Bool(True)
    use_ygrid = Bool(True)
    xtick_font = Property
    xtick_fontsize = Enum(*SIZES)
    xtick_fontname = Enum(*FONTS)
    xtick_in = Int(1)
    xtick_out = Int(5)

    xtitle_font = Property
    xtitle_fontsize = Enum(*SIZES)
    xtitle_fontname = Enum(*FONTS)

    ytick_font = Property
    ytick_fontsize = Enum(*SIZES)
    ytick_fontname = Enum(*FONTS)
    ytick_in = Int(1)
    ytick_out = Int(5)

    ytitle_font = Property
    ytitle_fontsize = Enum(*SIZES)
    ytitle_fontname = Enum(*FONTS)

    groups = List
    # group = Property
    # group_editor_klass = None
    group_options_klass = None
    # refresh_colors = Event

    xpadding = Property
    xpad = Float
    xpad_as_percent = Bool
    use_xpad = Bool

    omit_by_tag = Bool(True)

    def initialize(self):
        if not self.groups:
            self.groups = self._groups_default()

    def paddings(self):
        return self.padding_left, self.padding_right, self.padding_top, self.padding_bottom

    def get_group_colors(self):
        return [gi.color for gi in self.groups]

    def get_group(self, gid):
        n = len(self.groups)
        return self.groups[gid % n]

    def generate_title(self, analyses, n):
        attrs = self.title_attribute_keys
        ts = []
        rref, ctx = None, {}
        material_map = {'Groundmass concentrate': 'GMC',
                        'Kaersutite': 'Kaer',
                        'Plagioclase': 'Plag',
                        'Sanidine': 'San'}

        for gid, ais in groupby(analyses, key=lambda x: x.group_id):
            ref = ais.next()
            d = {}
            for ai in attrs:
                if ai == 'alphacounter':
                    v = ALPHAS[n]
                elif ai == 'numericcounter':
                    v = n
                else:
                    v = getattr(ref, ai)
                    if ai == 'material':
                        try:
                            v = material_map[v]
                        except KeyError:
                            pass
                d[ai] = v

            if not rref:
                rref = ref
                ctx = d

            ts.append(self.title_formatter.format(**d))

        t = self.title_delimiter.join(ts)
        lt = self.title_leading_text
        if lt:
            if lt.lower() in ctx:
                lt = ctx[lt.lower()]
            t = '{} {}'.format(lt, t)

        tt = self.title_trailing_text
        if tt:
            if tt.lower() in ctx:
                tt = ctx[tt.lower()]
            t = '{} {}'.format(t, tt)

        return t

    # private
    def _groups_default(self):
        if self.group_options_klass:
            return [self.group_options_klass(color=ci,
                                             line_color=ci,
                                             group_id=i) for i, ci in enumerate(colornames)]
        else:
            return []

    def _edit_title_format_button_fired(self):
        from pychron.processing.label_maker import TitleTemplater, TitleTemplateView

        tm = TitleTemplater(label=self.title,
                            delimiter=self.title_delimiter,
                            leading_text=self.title_leading_text,
                            trailing_text=self.title_trailing_text)

        tv = TitleTemplateView(model=tm)
        info = tv.edit_traits()
        if info.result:
            self.title_formatter = tm.formatter
            self.title_attribute_keys = tm.attribute_keys
            self.title_leading_text = tm.leading_text
            self.title_trailing_text = tm.trailing_text
            self.title = tm.label
            self.title_delimiter = tm.delimiter

    # ===============================================================================
    # property get/set
    # ===============================================================================
    def _get_xtick_font(self):
        return self._get_font('xtick', default_size=10)

    def _get_xtitle_font(self):
        return self._get_font('xtitle', default_size=12)

    def _get_ytick_font(self):
        return self._get_font('ytick', default_size=10)

    def _get_ytitle_font(self):
        return self._get_font('ytitle', default_size=12)

    def _get_font(self, name, default_size=10):
        xn = getattr(self, '{}_fontname'.format(name))
        xs = getattr(self, '{}_fontsize'.format(name))
        if xn is None:
            xn = FONTS[0]
        if xs is None:
            xs = default_size
        return '{} {}'.format(xn, xs)

        # return str_to_font('{} {}'.format(xn, xs))

    # def _get_group(self):
    #     if self.groups:
    #         return self.groups[0]

    def _get_xpadding(self):
        if self.use_xpad:
            return str(self.xpad) if self.xpad_as_percent else self.xpad


class AuxPlotFigureOptions(FigureOptions):
    aux_plots = List
    aux_plot_klass = AuxPlot

    def get_loadable_aux_plots(self):
        return reversed([pi for pi in self.aux_plots
                         if pi.name and pi.name != NULL_STR and (pi.save_enabled or pi.plot_enabled)])

    def get_saveable_aux_plots(self):
        # for a in self.aux_plots:
        # print a.name, a.save_enabled

        return list(reversed([pi for pi in self.aux_plots
                              if pi.name and pi.name != NULL_STR and pi.save_enabled]))

    def get_plotable_aux_plots(self):
        return list(reversed([pi for pi in self.aux_plots
                              if pi.name and pi.name != NULL_STR and pi.plot_enabled]))

    def _aux_plots_default(self):
        return [self.aux_plot_klass() for _ in range(12)]


class AgeOptions(AuxPlotFigureOptions):
    error_calc_method = Enum(*ERROR_TYPES)
    include_j_error = Bool(False)
    include_j_error_in_mean = Bool(True)
    include_irradiation_error = Bool(True)
    include_decay_error = Bool(False)

    nsigma = Enum(1, 2, 3)
    show_info = Bool(True)
    show_mean_info = Bool(True)
    show_error_type_info = Bool(True)
    label_box = Bool(False)

    index_attr = Str('uage')

    analysis_label_format = Str
    analysis_label_display = Str

    error_info_font = Property
    error_info_fontname = Enum(*FONTS)
    error_info_fontsize = Enum(*SIZES)

    label_font = Property
    label_fontname = Enum(*FONTS)
    label_fontsize = Enum(*SIZES)

    display_inset = Bool
    inset_width = Int(100)
    inset_height = Int(100)
    inset_location = Enum('Upper Right', 'Upper Left', 'Lower Right', 'Lower Left')

    def make_legend_key(self, ident, sample):
        key = ident
        if self.include_sample_in_legend:
            key = '{}({})'.format(sample, ident)
        return key

    def _include_j_error_changed(self, new):
        if new:
            self.include_j_error_in_mean = False

    def _get_label_font(self):
        return '{} {}'.format(self.label_fontname, self.label_fontsize)

    def _get_error_info_font(self):
        return '{} {}'.format(self.error_info_fontname,
                              self.error_info_fontsize)

# ============= EOF =============================================
