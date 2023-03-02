# ===============================================================================
# Copyright 2019 ross
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


# ============= EOF =============================================
from traits.has_traits import HasTraits
from traits.trait_types import List, Str, Instance, Int, Bool, Enum
from traitsui.editors.api import EnumEditor, TableEditor, InstanceEditor
from traitsui.group import VGroup, HGroup, Tabbed
from traitsui.item import Item, UItem
from traitsui.table_column import ObjectColumn
from traitsui.view import View

from pychron.core.pychron_traits import BorderVGroup
from pychron.core.ui.table_configurer import (
    TableConfigurer,
    get_columns_group,
    TableConfigurerHandler,
)
from pychron.pychron_constants import ARGON_KEYS, SIZES


class IsotopeTableConfigurer(TableConfigurer):
    id = "recall.isotopes"

    def traits_view(self):
        v = View(
            BorderVGroup(
                get_columns_group(),
                Item("font", enabled_when="fontsize_enabled"),
                label="Isotopes",
            )
        )
        return v


class IntermediateTableConfigurer(TableConfigurer):
    id = "recall.intermediate"


class Ratio(HasTraits):
    isotopes = List([""] + list(ARGON_KEYS))
    numerator = Str
    denominator = Str

    @property
    def tagname(self):
        if self.numerator and self.denominator:
            return "{}/{}".format(self.numerator, self.denominator)

    def get_dump(self):
        return {"numerator": self.numerator, "denominator": self.denominator}


class CocktailOptions(HasTraits):
    ratios = List

    def get_dump(self):
        return {"ratios": [r.get_dump() for r in self.ratios]}

    def set_ratios(self, ratios):
        self.ratios = [
            Ratio(numerator=r["numerator"], denominator=r["denominator"])
            for r in ratios
        ]

    def _ratios_default(self):
        return [Ratio() for i in range(10)]

    def traits_view(self):
        cols = [
            ObjectColumn(name="numerator", editor=EnumEditor(name="isotopes")),
            ObjectColumn(name="denominator", editor=EnumEditor(name="isotopes")),
        ]
        v = View(
            BorderVGroup(
                UItem("ratios", editor=TableEditor(sortable=False, columns=cols)),
                label="Cocktail Options",
            )
        )
        return v


class RecallOptions(HasTraits):
    cocktail_options = Instance(CocktailOptions, ())
    isotope_sig_figs = Int(5)
    computed_sig_figs = Int(5)
    intermediate_sig_figs = Int(5)

    def set_cocktail(self, co):
        cc = CocktailOptions()
        cc.set_ratios(co.get("ratios"))
        self.cocktail_options = cc

    def get_dump(self):
        return {
            "cocktail_options": self.cocktail_options.get_dump(),
            "computed_sig_figs": self.computed_sig_figs,
            "sig_figs": self.isotope_sig_figs,
            "intermediate_sig_figs": self.intermediate_sig_figs,
        }

    def traits_view(self):
        v = View(
            Item("computed_sig_figs", label="Main SigFigs"),
            Item("isotope_sig_figs", label="Isotope SigFigs"),
            Item("intermediate_sig_figs", label="Intermediate SigFigs"),
            UItem("cocktail_options", style="custom"),
        )
        return v


class RecallTableConfigurer(TableConfigurer):
    isotope_table_configurer = Instance(IsotopeTableConfigurer, ())
    intermediate_table_configurer = Instance(IntermediateTableConfigurer, ())
    show_intermediate = Bool
    experiment_fontsize = Enum(*SIZES)
    measurement_fontsize = Enum(*SIZES)
    extraction_fontsize = Enum(*SIZES)
    main_measurement_fontsize = Enum(*SIZES)
    main_extraction_fontsize = Enum(*SIZES)
    main_computed_fontsize = Enum(*SIZES)

    subview_names = ("experiment", "measurement", "extraction")
    main_names = ("measurement", "extraction", "computed")
    bind_fontsizes = Bool(False)
    global_fontsize = Enum(*SIZES)

    recall_options = Instance(RecallOptions, ())

    def _get_dump(self):
        obj = super(RecallTableConfigurer, self)._get_dump()
        obj["show_intermediate"] = self.show_intermediate
        for a in self.subview_names:
            a = "{}_fontsize".format(a)
            obj[a] = getattr(self, a)

        for a in self.main_names:
            a = "main_{}_fontsize".format(a)
            obj[a] = getattr(self, a)

        for attr in ("global_fontsize", "bind_fontsizes"):
            obj[attr] = getattr(self, attr)

        obj["recall_options"] = self.recall_options.get_dump()
        return obj

    def _load_hook(self, obj):
        self.show_intermediate = obj.get("show_intermediate", True)
        self.isotope_table_configurer.load()
        self.intermediate_table_configurer.load()

        for a in self.subview_names:
            a = "{}_fontsize".format(a)
            setattr(self, a, obj.get(a, 10))

        for a in self.main_names:
            a = "main_{}_fontsize".format(a)
            setattr(self, a, obj.get(a, 10))

        for attr in ("global_fontsize", "bind_fontsizes"):
            try:
                setattr(self, attr, obj[attr])
            except KeyError:
                pass

        recall_options = obj.get("recall_options")
        if recall_options:
            r = RecallOptions()
            r.set_cocktail(recall_options.get("cocktail_options"))
            for tag in ("intermediate", "isotope", "computed"):
                tag = "{}_sig_figs".format(tag)
                setattr(r, tag, recall_options.get(tag, 5))

            self.recall_options = r

    def dump(self):
        super(RecallTableConfigurer, self).dump()
        self.intermediate_table_configurer.dump()
        self.isotope_table_configurer.dump()

    def set_columns(self):
        self.isotope_table_configurer.set_columns()
        self.intermediate_table_configurer.set_columns()

        self.isotope_table_configurer.update()
        self.intermediate_table_configurer.update()

    def set_font(self):
        self.isotope_table_configurer.set_font()
        self.intermediate_table_configurer.set_font()

    def set_fonts(self, av):
        self.set_font()

        for a in self.subview_names:
            s = getattr(self, "{}_fontsize".format(a))
            av.update_fontsize(a, s)

        for a in self.main_names:
            av.update_fontsize(
                "main.{}".format(a), getattr(self, "main_{}_fontsize".format(a))
            )

        av.main_view.refresh_needed = True

    def _bind_fontsizes_changed(self, new):
        if new:
            self._global_fontsize_changed()
        self.isotope_table_configurer.fontsize_enabled = not new
        self.intermediate_table_configurer.fontsize_enabled = not new

    def _global_fontsize_changed(self):
        gf = self.global_fontsize
        self.isotope_table_configurer.font = gf
        self.intermediate_table_configurer.font = gf

        self.main_measurement_fontsize = gf
        self.main_extraction_fontsize = gf
        self.main_computed_fontsize = gf

    def traits_view(self):
        main_grp = VGroup(
            HGroup(
                Item("bind_fontsizes"),
                Item("global_fontsize", enabled_when="bind_fontsizes"),
            ),
            Item("main_extraction_fontsize", enabled_when="not bind_fontsizes"),
            Item("main_measurement_fontsize", enabled_when="not bind_fontsizes"),
            Item("main_computed_fontsize", enabled_when="not bind_fontsizes"),
        )

        main_view = VGroup(
            main_grp,
            UItem("isotope_table_configurer", style="custom"),
            HGroup(Item("show_intermediate", label="Show Intermediate Table")),
            UItem(
                "intermediate_table_configurer",
                style="custom",
                enabled_when="show_intermediate",
            ),
            label="Main",
        )

        # experiment_view = VGroup(Item('experiment_fontsize', label='Size'),
        #                          show_border=True,
        #                          label='Experiment')
        # measurement_view = VGroup(Item('measurement_fontsize', label='Size'),
        #                           show_border=True,
        #                           label='Measurement')
        # extraction_view = VGroup(Item('extraction_fontsize', label='Size'),
        #                          show_border=True,
        #                          label='Extraction')

        v = View(
            Tabbed(
                main_view,
                UItem("recall_options", editor=InstanceEditor(), style="custom"),
                # VGroup(experiment_view,
                #        measurement_view,
                #        extraction_view, label='Scripts')
            ),
            buttons=["OK", "Cancel", "Revert"],
            kind="livemodal",
            title="Configure Table",
            handler=TableConfigurerHandler,
            resizable=True,
            width=300,
        )
        return v
