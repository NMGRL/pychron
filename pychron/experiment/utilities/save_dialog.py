# ===============================================================================
# Copyright 2016 Jake Ross
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
from __future__ import absolute_import

import os

from traits.api import HasTraits, Bool, Directory, Int, Str
from traitsui.api import HGroup, VGroup, Item, UItem

from pychron.core.helpers.filetools import add_extension
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.ui.strings import PascalCase, SpacelessStr, ExperimentStr


class BaseSaveDialog(HasTraits):
    root = Directory

    @property
    def path(self):
        if self.root and self.name:
            return os.path.join(self.root, add_extension(self.name, ".txt"))


class IncrementalHeatTemplateSaveDialog(BaseSaveDialog):
    fname = SpacelessStr()
    n = Int

    def get_path(self):
        info = self.edit_traits()
        if info.result:
            return self.path

    @property
    def name(self):
        return "{:02n}-{}".format(self.n, self.fname)

    def traits_view(self):
        ngrp = HGroup(
            Item(
                "fname",
                tooltip="No spaces in name. Name is automatically prefixed with the number of steps",
            )
        )
        dgrp = HGroup(Item("root", label="Directory"))
        v = okcancel_view(
            VGroup(ngrp, dgrp), width=400, title="Save Step Heat Template"
        )
        return v


class ExperimentSaveDialog(BaseSaveDialog):
    # name = PascalCase()
    name = ExperimentStr
    use_current_exp = Bool

    help_str = Str(
        "<b>Name must be in PascalCase. NoSpaces and only AlphaNumeric characters</b>"
    )

    def _use_current_exp_changed(self, new):
        if new:
            self.name = "CurrentExperiment"

    def traits_view(self):
        ngrp = HGroup(
            Item(
                "name",
                tooltip="Name must be in PascalCase. NoSpaces, use only AlphaNumeric. "
                'This is "PascalCase". This is not "pascalcase"',
            ),
            Item("use_current_exp"),
        )
        dgrp = HGroup(Item("root", label="Directory"))
        hgrp = UItem("help_str", style="readonly")

        v = okcancel_view(VGroup(ngrp, hgrp, dgrp), width=400, title="Save Experiment")
        return v


# ============= EOF =============================================
