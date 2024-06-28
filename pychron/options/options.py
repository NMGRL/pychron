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
import importlib
import json

from chaco.axis import DEFAULT_TICK_FORMATTER
from chaco.axis_view import float_or_auto
from enable.markers import marker_names
from pyface.message_dialog import warning
from traits.api import (
    HasTraits,
    Str,
    Int,
    Bool,
    Float,
    Property,
    Enum,
    List,
    Range,
    Color,
    Button,
    Instance,
    Any,
)
from traits.trait_errors import TraitError
from traitsui.api import (
    View,
    Item,
    HGroup,
    VGroup,
    EnumEditor,
    TableEditor,
    Spring,
    Group,
    spring,
    UItem,
    ListEditor,
    InstanceEditor,
    CheckListEditor,
    TextEditor,
)
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.handler import Controller
from traitsui.table_column import ObjectColumn

from pychron.core.helpers.color_generators import colornames
from pychron.core.helpers.formatting import floatfmt
from pychron.core.helpers.iterfuncs import groupby_group_id
from pychron.core.pychron_traits import BorderHGroup, BorderVGroup
from pychron.core.ui.table_editor import myTableEditor
from pychron.core.utils import alphas
from pychron.core.yaml import yload
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.options.aux_plot import AuxPlot
from pychron.options.guide import Guide, RangeGuide
from pychron.options.layout import FigureLayout
from pychron.processing.j_error_mixin import JErrorMixin
from pychron.pychron_constants import NULL_STR, ERROR_TYPES, FONTS, SIZES, SIG_FIGS


def importklass(klass):
    args = klass[8:-2].split(".")
    mod = ".".join(args[:-1])
    mod = importlib.import_module(mod)
    return getattr(mod, args[-1])


def _table_column(klass, *args, **kw):
    kw["text_font"] = "arial 10"
    return klass(*args, **kw)


def object_column(*args, **kw):
    return _table_column(ObjectColumn, *args, **kw)


def checkbox_column(*args, **kw):
    return _table_column(CheckboxColumn, *args, **kw)


class SubOptions(Controller):
    # traits_view = View(Item('index_attr', label='Foo'))
    def _make_view(self, *args, **kw):
        if "scrollable" not in kw:
            kw["scrollable"] = True
        return View(*args, **kw)


class TitleSubOptions(SubOptions):
    def traits_view(self):
        v = self._make_view(self._get_title_group())
        return v

    def _get_title_group(self):
        a = HGroup(UItem("title_fontname"), UItem("title_fontsize"))
        b = HGroup(
            Item(
                "auto_generate_title",
                tooltip="Auto generate a title based on the analysis list",
            ),
            Item(
                "title",
                springy=False,
                enabled_when="not auto_generate_title",
                tooltip="User specified plot title",
            ),
            icon_button_editor(
                "edit_title_format_button", "cog", enabled_when="auto_generate_title"
            ),
        )

        title_grp = BorderVGroup(a, b, label="Title")
        return title_grp


class GroupSubOptions(SubOptions):
    def _make_group(self):
        return (
            UItem(
                "groups",
                style="custom",
                editor=ListEditor(
                    mutable=False, style="custom", editor=InstanceEditor()
                ),
            ),
        )

    def traits_view(self):
        g = self._make_group()
        # buttons=['OK', 'Cancel', 'Revert'],
        # kind='livemodal', resizable=True,
        # height=700,
        # title='Group Attributes')
        return self._make_view(g)


class AppearanceSubOptions(SubOptions):
    def _get_nominal_group(self):
        return HGroup(self._get_bg_group(), self._get_grid_group())

    def _get_layout_group(self):
        return VGroup(UItem("layout", style="custom"))

    def _get_xfont_group(self):
        v = VGroup(
            self._create_axis_group("x", "title"),
            self._create_axis_group("x", "tick"),
            show_border=True,
            label="X Axis",
        )
        return v

    def _get_yfont_group(self):
        v = VGroup(
            self._create_axis_group("y", "title"),
            self._create_axis_group("y", "tick"),
            show_border=True,
            label="Y Axis",
        )
        return v

    def _create_axis_group(self, axis, name):
        hg = HGroup(
            Item("{}{}_fontname".format(axis, name), label=name.capitalize()),
            Item("{}{}_fontsize".format(axis, name), show_label=False),
        )
        return hg

    def _get_margin_group(self):
        return BorderVGroup(
            HGroup(
                Spring(springy=False, width=100),
                Item("margin_top", label="Top"),
                spring,
            ),
            HGroup(
                Item("margin_left", label="Left"), Item("margin_right", label="Right")
            ),
            HGroup(
                Spring(springy=False, width=100),
                Item("margin_bottom", label="Bottom"),
                spring,
            ),
            label="Page Margins",
        )

    def _get_padding_group(self):
        return BorderVGroup(
            HGroup(
                Spring(springy=False, width=100),
                Item("padding_top", label="Top"),
                spring,
            ),
            HGroup(
                Item("padding_left", label="Left"), Item("padding_right", label="Right")
            ),
            HGroup(
                Spring(springy=False, width=100),
                Item("padding_bottom", label="Bottom"),
                spring,
            ),
            Item(
                "plot_spacing", label="Spacing", tooltip="Space between plots in pixels"
            ),
            enabled_when="not formatting_options",
            label="Padding/Spacing",
        )

    def _get_bg_group(self):
        grp = Group(
            Item("bgcolor", label="Figure"),
            Item("plot_bgcolor", label="Plot"),
            show_border=True,
            enabled_when="not formatting_options",
            label="Background",
        )
        return grp

    def _get_grid_group(self):
        grid_grp = VGroup(
            Item("use_xgrid", label="XGrid Visible"),
            Item("use_ygrid", label="YGrid Visible"),
            show_border=True,
            label="Grid",
        )
        return grid_grp

    def traits_view(self):
        fgrp = VGroup(
            UItem("fontname"),
            HGroup(self._get_xfont_group(), self._get_yfont_group()),
            label="Fonts",
            show_border=True,
        )

        g = VGroup(
            self._get_bg_group(),
            self._get_layout_group(),
            self._get_margin_group(),
            self._get_padding_group(),
            self._get_grid_group(),
        )

        return self._make_view(VGroup(g, fgrp))


class MainOptions(SubOptions):
    def _get_columns(self):
        cols = [
            checkbox_column(name="plot_enabled", label="Use"),
            object_column(name="name", editor=EnumEditor(name="names")),
            object_column(name="scale"),
            object_column(name="height", format_func=lambda x: str(x) if x else ""),
            checkbox_column(name="show_labels", label="Labels"),
            checkbox_column(name="x_error", label="X Err."),
            checkbox_column(name="y_error", label="Y Err."),
            object_column(name="ytitle", label="Y Title"),
            checkbox_column(name="ytick_visible", label="Y Tick"),
            checkbox_column(name="ytitle_visible", label="Y Title Visible"),
            checkbox_column(name="y_axis_right", label="Y Right"),
            checkbox_column(name="yticks_both_sides", label="Y Ticks Both"),
            object_column(
                name="scalar",
                label="Multiplier",
                format_func=lambda x: floatfmt(x, n=2, s=2, use_scientific=True),
            ),
            checkbox_column(name="has_filter", label="Filter", editable=False),
            # object_column(name='filter_str', label='Filter')
        ]

        return cols

    def _get_name_grp(self):
        grp = BorderVGroup(
            HGroup(
                Item("name", editor=EnumEditor(name="names")),
                Item("ytitle", label="Y Title"),
            ),
            HGroup(
                Item("scale", editor=EnumEditor(values=["linear", "log"])),
                Item("height"),
            ),
        )
        return grp

    def _get_yticks_grp(self):
        g = (
            BorderHGroup(
                Item("use_sparse_yticks", label="Sparse"),
                Item(
                    "sparse_yticks_step", label="Step", enabled_when="use_sparse_yticks"
                ),
                Item(
                    "ytick_interval",
                    label="Interval",
                    editor=TextEditor(evaluate=float_or_auto),
                ),
                label="Y Ticks",
            ),
        )
        return g

    def _get_ylimits_group(self):
        g = BorderHGroup(
            Item("ymin", label="Min"),
            Item("ymax", label="Max"),
            icon_button_editor("clear_ylimits_button", "clear"),
            label="Y Limits",
        )
        return g

    def _get_marker_group(self):
        g = BorderHGroup(
            UItem("marker", editor=EnumEditor(values=marker_names)),
            Item("marker_size", label="Size"),
            UItem("marker_color"),
            label="Marker",
        )
        return g

    def _get_edit_view(self):
        v = View(
            VGroup(
                self._get_name_grp(),
                self._get_yticks_grp(),
                self._get_ylimits_group(),
                self._get_marker_group(),
            )
        )
        return v

    def _get_analysis_group(self):
        return HGroup(
            UItem(
                "analysis_types",
                style="custom",
                editor=CheckListEditor(name="available_types"),
            ),
            show_border=True,
            label="Analysis Types",
        )

    def _get_global_group(self):
        return

    def traits_view(self):
        aux_plots_grp = Item(
            "aux_plots",
            style="custom",
            width=525,
            show_label=False,
            editor=myTableEditor(
                columns=self._get_columns(),
                sortable=False,
                # deletable=True,
                clear_selection_on_dclicked=True,
                orientation="vertical",
                selected="selected",
                selection_mode="rows",
                edit_view=self._get_edit_view(),
                reorderable=False,
            ),
        )
        global_grp = self._get_global_group()
        if global_grp:
            v = self._make_view(global_grp, aux_plots_grp)
        else:
            v = self._make_view(aux_plots_grp)
        return v


# ===============================================================
# ===============================================================


def convert_color(ss):
    from pyface.qt.QtGui import QColor

    nd = {}
    for k, v in ss.items():
        if isinstance(v, QColor):
            nd[k] = v.rgba()
    ss.update(**nd)


class BaseOptions(HasTraits):
    fontname = Enum(*FONTS)
    _main_options_klass = MainOptions
    subview_names = List(transient=True)
    manager_id = Str
    _subview_cache = None

    def make_state(self):
        state = self.__getstate__()
        state["klass"] = str(self.__class__)

        try:
            layout = state.pop("layout")
            if layout:
                state["layout"] = str(layout.__class__), layout.__getstate__()
        except KeyError:
            pass

        tags = ("groups", "aux_plots", "selected", "guides", "ranges")
        atags = self._get_tags()
        if atags:
            tags += atags

        for tag in tags:
            try:
                items = state.pop(tag)
                if items:

                    def func(gi):
                        s = gi.__getstate__()
                        convert_color(s)
                        return str(gi.__class__), s

                    ngs = [func(gi) for gi in items]
                    state[tag] = ngs
            except KeyError as e:
                pass

        convert_color(state)
        self._get_state_hook(state)
        convert_color(state)

        return state

    def dump(self, wfile):
        state = self.make_state()
        json.dump(state, wfile, indent=4, sort_keys=True)

    def _get_state_hook(self, state):
        pass

    def _load_state_hook(self, state):
        pass

    def load(self, state):
        state.pop("klass")

        def inst(klass, key=None):
            klass, ctx = klass
            cls = importklass(klass)
            if key == "aux_plots":
                if "_plot_names" in ctx:
                    ctx.pop("_plot_names")
                elif "error_types" in ctx:
                    ctx.pop("error_types")

            return cls(**ctx)

        if "layout" in state:
            layout = state.pop("layout")
            try:
                obj = inst(layout)
                state["layout"] = obj
            except ValueError:
                pass

        tags = ("aux_plots", "groups", "selected", "guides", "ranges")
        atags = self._get_tags()
        if atags:
            tags += atags
        for key in tags:
            if key in state:
                state[key] = [inst(a, key) for a in state.pop(key)]

        self._load_state_hook(state)
        try:
            self.__setstate__(state)
        except BaseException:
            try:
                self._setstate(state)
            except BaseException:
                warning(
                    None,
                    "Pychron options changed and your saved options are incompatible.  Unable to fully load. "
                    "You will need to check/rebuild this saved options set",
                )

    def _get_tags(self):
        return None

    def _setstate(self, state):
        # see self.__setstate___

        self._init_trait_listeners()
        for k, v in state.items():
            try:
                self.trait_set(trait_change_notify=True, **{k: v})
            except BaseException:
                continue

        self._post_init_trait_listeners()
        self.traits_init()

        self.traits_inited(True)

    def get_cached_subview(self, name):
        if self._subview_cache is None:
            self._subview_cache = {}

        try:
            return self._subview_cache[name]
        except KeyError:
            v = self.get_subview(name)
            self._subview_cache[name] = v
            return v

    def to_dict(self):
        keys = [
            trait
            for trait in self.traits()
            if not trait.startswith("trait")
            and not trait.endswith("button")
            and self.to_dict_test(trait)
        ]

        return {key: self.formatted_attr(key) for key in keys}

    def formatted_attr(self, key):
        obj = getattr(self, key)
        if "color" in key:
            obj = obj.red(), obj.green(), obj.blue(), obj.alpha()
        return obj

    def to_dict_test(self, k):
        return True

    def load_factory_defaults(self, path):
        if path:
            yd = yload(path)
            self._load_factory_defaults(yd)

    def setup(self):
        pass

    def setup_groups(self):
        pass

    def initialize(self):
        pass

    def set_names(self, names):
        pass

    def set_detectors(self, dets):
        pass

    def set_analysis_types(self, atypes):
        pass

    def _fontname_changed(self):
        self._set_fonts(self.fontname)
        for attr in self.traits():
            if attr.endswith("_fontname"):
                setattr(self, attr, self.fontname)

    def _set_fonts(self, name):
        pass

    def get_subview(self, name):
        name = name.lower()

        if name == "main":
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
                try:
                    setattr(self, k, v)
                except TraitError as e:
                    print("failed setting factory default. {}, {}, {}".format(k, v, e))


class GroupMixin(HasTraits):
    group_options_klass = None
    groups = List

    def setup(self):
        if self.group_options_klass:
            if len(self.groups) < len(colornames):
                start = len(self.groups)
                new_groups = [
                    self.group_options_klass(
                        color=ci, line_color=ci, group_id=start + i
                    )
                    for i, ci in enumerate(colornames[start:])
                ]
                self.groups.extend(new_groups)

    def _groups_default(self):
        if self.group_options_klass:
            return [
                self.group_options_klass(color=ci, line_color=ci, group_id=i)
                for i, ci in enumerate(colornames)
            ]
        else:
            return []


class FigureOptions(BaseOptions, GroupMixin):
    bgcolor = Color
    plot_bgcolor = Color
    plot_spacing = Range(0, 50)
    padding_left = Int(100)
    padding_right = Int(100)
    padding_top = Int(100)
    padding_bottom = Int(100)

    margin_left = Int(10)
    margin_right = Int(10)
    margin_top = Int(10)
    margin_bottom = Int(10)

    auto_generate_title = Bool
    include_legend = Bool(False)
    include_sample_in_legend = Bool
    legend_location = Enum("Upper Right", "Upper Left", "Lower Left", "Lower Right")
    title = Str
    title_formatter = Str
    title_attribute_keys = List
    title_delimiter = Str(",")
    title_leading_text = Str
    title_trailing_text = Str
    title_font = Property
    title_fontsize = Enum(*SIZES)
    title_fontname = Enum(*FONTS)
    edit_title_format_button = Button

    use_xgrid = Bool(True)
    use_ygrid = Bool(True)
    xtick_font = Property
    xtick_fontsize = Enum(*SIZES)
    xtick_fontname = Enum(*FONTS)
    xtick_in = Int(1)
    xtick_out = Int(5)
    xtick_label_formatter = Property
    xtick_label_format_str = Str

    xtitle_font = Property
    xtitle_fontsize = Enum(*SIZES)
    xtitle_fontname = Enum(*FONTS)
    xtitle = Str

    ytick_font = Property
    ytick_fontsize = Enum(*SIZES)
    ytick_fontname = Enum(*FONTS)
    ytick_in = Int(1)
    ytick_out = Int(5)
    ytick_label_formatter = Property
    ytick_label_format_str = Str

    ytitle_font = Property
    ytitle_fontsize = Enum(*SIZES)
    ytitle_fontname = Enum(*FONTS)

    layout = Instance(FigureLayout, ())
    guides = List
    ranges = List
    # group = Property
    # group_editor_klass = None

    # refresh_colors = Event
    stretch_vertical = Bool
    xpadding = Property
    xpad = Float
    xpad_as_percent = Bool
    use_xpad = Bool

    omit_by_tag = Bool(True)

    # def initialize(self):
    #     if not self.groups:
    #         self.groups = self._groups_default()
    def get_page_size(self):
        fw, fh = self.layout.fixed_width, self.layout.fixed_height
        if fw or fh:
            return fw, fh

    def get_page_margins(self):
        return self.margin_left, self.margin_right, self.margin_top, self.margin_bottom

    def get_paddings(self):
        return (
            self.padding_left,
            self.padding_right,
            self.padding_top,
            self.padding_bottom,
        )

    def get_group_colors(self):
        return [gi.color for gi in self.groups]

    def get_group(self, gid):
        n = len(self.groups)
        return self.groups[gid % n]

    def generate_title(self, analyses, n):
        attrs = self.title_attribute_keys
        ts = []
        rref, ctx = None, {}
        material_map = {
            "Groundmass concentrate": "GMC",
            "Kaersutite": "Kaer",
            "Plagioclase": "Plag",
            "Sanidine": "San",
        }

        for gid, ais in groupby_group_id(analyses):
            ref = next(ais)
            d = {}
            for ai in attrs:
                if ai == "alphacounter":
                    v = alphas(n)
                elif ai == "numericcounter":
                    v = n
                elif ai == "<space>":
                    v = " "
                elif ai == "runid":
                    v = ref.record_id
                else:
                    v = getattr(ref, ai)
                    if ai == "material":
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
            t = "{} {}".format(lt, t)

        tt = self.title_trailing_text
        if tt:
            if tt.lower() in ctx:
                tt = ctx[tt.lower()]
            t = "{} {}".format(t, tt)

        return t

    # private

    def _edit_title_format_button_fired(self):
        from pychron.options.label_maker import TitleTemplater, TitleTemplateView

        tm = TitleTemplater(
            label=self.title,
            delimiter=self.title_delimiter,
            leading_text=self.title_leading_text,
            trailing_text=self.title_trailing_text,
        )

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
    def _get_xtick_label_formatter(self):
        return self._get_tick_label_formatter(self.xtick_label_format_str)

    def _get_ytick_label_formatter(self):
        return self._get_tick_label_formatter(self.ytick_label_format_str)

    def _get_title_font(self):
        return self._get_font("title", default_size=12)

    def _get_xtick_font(self):
        return self._get_font("xtick", default_size=10)

    def _get_xtitle_font(self):
        return self._get_font("xtitle", default_size=12)

    def _get_ytick_font(self):
        return self._get_font("ytick", default_size=10)

    def _get_ytitle_font(self):
        return self._get_font("ytitle", default_size=12)

    def _get_tick_label_formatter(self, f):
        func = DEFAULT_TICK_FORMATTER

        if f.isdigit():
            f = "{{:0.{}f}}".format(f)

            def func(x):
                return f.format(x)

        return func

    def _get_font(self, name, default_size=10):
        xn = getattr(self, "{}_fontname".format(name))
        xs = getattr(self, "{}_fontsize".format(name))
        if xn is None:
            xn = FONTS[0]
        if xs is None:
            xs = default_size
        return "{} {}".format(xn, xs)

        # return str_to_font('{} {}'.format(xn, xs))

    # def _get_group(self):
    #     if self.groups:
    #         return self.groups[0]

    def _get_xpadding(self):
        if self.use_xpad:
            return str(self.xpad) if self.xpad_as_percent else self.xpad


NAUX_PLOTS = 15


class AuxPlotFigureOptions(FigureOptions):
    aux_plots = List
    aux_plot_klass = AuxPlot
    selected = List

    error_info_font = Property
    error_info_fontname = Enum(*FONTS)
    error_info_fontsize = Enum(*SIZES)
    naux_plots = Int(15)

    x_end_caps = Bool(False)
    y_end_caps = Bool(False)
    error_bar_nsigma = Enum(1, 2, 3)
    error_bar_line_width = Float(1.0)

    def setup(self):
        super(AuxPlotFigureOptions, self).setup()
        while len(self.aux_plots) > self.naux_plots:
            p = next(
                (pp for pp in self.aux_plots if not pp.name or not pp.plot_enabled),
                None,
            )
            if not p:
                break

            self.aux_plots.remove(p)

        while 1:
            if len(self.aux_plots) >= self.naux_plots:
                break

            aux = self.aux_plot_klass()
            self.aux_plots.append(aux)

    # def add_aux_plot(self, name, i=0, **kw):
    #     plt = self.aux_plot_klass(name=name, **kw)
    #     plt.plot_enabled = True
    #     try:
    #         self.aux_plots[i] = plt
    #     except IndexError:
    #         self.aux_plots.append(plt)

    # def get_loadable_aux_plots(self):
    #     return reversed([pi for pi in self.aux_plots
    #                      if pi.name and pi.name != NULL_STR and (pi.save_enabled or pi.plot_enabled)])
    def get_aux_plot_names(self):
        return [pi.get_keyname() for pi in self.get_plotable_aux_plots()]

    def get_saveable_aux_plots(self):
        return list(
            reversed(
                [
                    pi
                    for pi in self.aux_plots
                    if pi.name and pi.name != NULL_STR and pi.save_enabled
                ]
            )
        )

    def get_plotable_aux_plots(self):
        return list(
            reversed(
                [
                    pi
                    for pi in self.aux_plots
                    if pi.name and pi.name != NULL_STR and pi.plot_enabled
                ]
            )
        )

    def _get_error_info_font(self):
        return "{} {}".format(self.error_info_fontname, self.error_info_fontsize)

    def _aux_plots_default(self):
        return [self.aux_plot_klass() for _ in range(NAUX_PLOTS)]


class AgeOptions(AuxPlotFigureOptions, JErrorMixin):
    error_calc_method = Enum(*ERROR_TYPES)
    # include_j_error = Bool(False)
    # include_j_error_in_mean = Bool(True)

    include_irradiation_error = Bool(True)
    include_decay_error = Bool(False)

    nsigma = Enum(1, 2, 3)
    show_info = Bool(True)
    show_mean_info = Bool(True)
    show_error_type_info = Bool(True)
    label_box = Bool(False)

    index_attr = Str("uage")

    analysis_label_format = Str
    analysis_label_display = Str

    label_font = Property
    label_fontname = Enum(*FONTS)
    label_fontsize = Enum(*SIZES)

    # inset
    display_inset = Bool
    inset_width = Int(100)
    inset_height = Int(100)
    inset_location = Enum("Upper Right", "Upper Left", "Lower Right", "Lower Left")
    inset_label_font = Property
    inset_label_fontname = Enum(*FONTS)
    inset_label_fontsize = Enum(*SIZES)

    inset_show_axes_titles = Bool(False)

    inset_x_bounds = Property
    inset_xmin = Float
    inset_xmax = Float

    inset_y_bounds = Property
    inset_ymin = Float
    inset_ymax = Float

    mswd_sig_figs = Enum(*SIG_FIGS)

    edit_label_format_button = Button

    def make_legend_key(self, ident, sample):
        key = ident
        if self.include_sample_in_legend:
            key = "{}({})".format(sample, ident)
        return key

    def _get_label_font(self):
        return "{} {}".format(self.label_fontname, self.label_fontsize)

    def _get_inset_label_font(self):
        return "{} {}".format(self.inset_label_fontname, self.inset_label_fontsize)

    def _get_inset_x_bounds(self):
        mi, ma = self.inset_xmin, self.inset_xmax
        return mi, ma

    def _get_inset_y_bounds(self):
        mi, ma = self.inset_ymin, self.inset_ymax
        return mi, ma

    def _edit_label_format_button_fired(self):
        from pychron.options.label_maker import LabelTemplater, LabelTemplateView

        lm = LabelTemplater(label=self.analysis_label_display)
        lv = LabelTemplateView(model=lm)
        info = lv.edit_traits()
        if info.result:
            self.analysis_label_format = lm.formatter
            self.analysis_label_display = lm.label
            # self.refresh_plot_needed = True


class GuidesOptions(SubOptions):
    add_guide_button = Button
    delete_guide_button = Button
    add_range_button = Button
    delete_range_button = Button
    selected = Any
    selected_range = Any

    def __init__(self, *args, **kw):
        super(GuidesOptions, self).__init__(*args, **kw)
        names = ["All Plots"] + list(reversed(self.model.get_aux_plot_names()))
        for g in self.model.guides:
            g.plotnames = names
        for g in self.model.ranges:
            g.plotnames = names

    def _add_guide_button_fired(self):
        if self.selected:
            g = Guide(**self.selected.to_kwargs())
        else:
            g = Guide()

        g.plotnames = ["All Plots"] + list(reversed(self.model.get_aux_plot_names()))
        self.model.guides.append(g)

    def _delete_guide_button_fired(self):
        if self.selected:
            self.model.guides.remove(self.selected)

    def _add_range_button_fired(self):
        if self.selected_range:
            g = RangeGuide(**self.selected_range.to_kwargs())
        else:
            g = RangeGuide()

        g.plotnames = ["All Plots"] + list(reversed(self.model.get_aux_plot_names()))
        self.model.ranges.append(g)

    def _delete_range_button_fired(self):
        if self.selected_range:
            self.model.ranges.remove(self.selected_range)

    def traits_view(self):
        cols = [
            CheckboxColumn(name="visible", label="Visible"),
            ObjectColumn(name="value", label="Value", width=200),
            ObjectColumn(name="minvalue", label="Min", width=200),
            ObjectColumn(name="maxvalue", label="Max", width=200),
            ObjectColumn(name="orientation", label="Orientation"),
            ObjectColumn(
                name="plotname", editor=EnumEditor(name="plotnames"), label="Plot"
            ),
            # ObjectColumn(name="alpha", label="Opacity"),
            # ObjectColumn(name="color", label="Color"),
            # ObjectColumn(name="line_style", label='Style'),
            # ObjectColumn(name="line_width", label='Width'),
        ]
        edit_view = View(
            Item("label", label="Label"),
            Item("alpha", label="Opacity"),
            UItem("color"),
            UItem("line_style", label="Style"),
            UItem("line_width", label="Width"),
        )

        rangecols = [
            CheckboxColumn(name="visible", label="Visible"),
            ObjectColumn(name="minvalue", label="Min", width=200),
            ObjectColumn(name="maxvalue", label="Max", width=200),
            ObjectColumn(name="orientation", label="Orientation"),
            ObjectColumn(
                name="plotname", editor=EnumEditor(name="plotnames"), label="Plot"
            ),
            # ObjectColumn(name="alpha", label="Opacity"),
            # ObjectColumn(name="color", label="Color"),
            # ObjectColumn(name="line_style", label='Style'),
            # ObjectColumn(name="line_width", label='Width'),
        ]
        return self._make_view(
            VGroup(
                BorderVGroup(
                    HGroup(
                        icon_button_editor("controller.add_guide_button", "add"),
                        icon_button_editor(
                            "controller.delete_guide_button",
                            "delete",
                            enabled_when="controller.selected",
                        ),
                    ),
                    UItem(
                        "guides",
                        editor=TableEditor(
                            columns=cols,
                            sortable=False,
                            edit_view=edit_view,
                            orientation="vertical",
                            selected="controller.selected",
                        ),
                    ),
                    label="Guides",
                ),
                BorderVGroup(
                    HGroup(
                        icon_button_editor("controller.add_range_button", "add"),
                        icon_button_editor(
                            "controller.delete_range_button",
                            "delete",
                            enabled_when="controller.selected",
                        ),
                    ),
                    UItem(
                        "ranges",
                        editor=TableEditor(
                            columns=rangecols,
                            sortable=False,
                            edit_view=edit_view,
                            orientation="vertical",
                            selected="controller.selected_range",
                        ),
                    ),
                    label="Ranges",
                ),
            )
        )


# ============= EOF =============================================
