# ===============================================================================
# Copyright 2018 ross
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
import os
import shutil
from operator import attrgetter

from traits.api import HasTraits, Float, Str, List, Bool, Property, Int, Enum
from traitsui.api import (
    View,
    UItem,
    Item,
    HGroup,
    ListEditor,
    EnumEditor,
    Label,
    InstanceEditor,
    VGroup,
)

from pychron.core.helpers.iterfuncs import groupby_repo, groupby_key
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.core.pychron_traits import BorderVGroup, StepStr, BorderHGroup
from pychron.core.utils import alpha_to_int
from pychron.dvc import NPATH_MODIFIERS, analysis_path, dvc_load, dvc_dump
from pychron.experiment.utilities.runid import make_runid
from pychron.pipeline.nodes.data import BaseDVCNode
from pychron.pychron_constants import PLUSMINUS


class ICFactor(HasTraits):
    num = Str
    det = Str
    detectors = List
    value = Float
    error = Float
    use = Bool
    enabled = Property
    mode = Enum("Direct", "Scale", "Transform")
    transform_variable = Enum("Ar40", "Ar39", "Ar38", "Ar37", "Ar36", "TotalIntensity")
    scaling_value = Float
    transform_coefficients = Str

    def _get_enabled(self):
        if self.use:
            if self.mode == "Direct":
                return self.value and self.error
            elif self.mode == "Scale":
                return self.scaling_value
            elif self.mode == "Transform":
                return self.transform_variable and self.transform_coefficients

    def traits_view(self):
        direct_grp = BorderHGroup(
            Item(
                "num",
                label="Relative To",
                editor=EnumEditor(name="detectors"),
            ),
            Item("value"),
            Label(PLUSMINUS),
            UItem("error"),
            visible_when='mode=="Direct"',
        )

        scale_grp = BorderHGroup(
            Item(
                "scaling_value",
            ),
            visible_when='mode=="Scale"',
        )
        transform_grp = BorderHGroup(
            Item("transform_variable", label="Variable"),
            Item(
                "transform_coefficients",
                tooltip="Define coefficients as a comma separated list of values. e.g. 3,2,"
                "1 is equivalent to 3x^2 + 2x + 1",
                label="Coefficients",
            ),
            visible_when='mode=="Transform"',
        )

        v = View(
            BorderVGroup(
                BorderHGroup(
                    UItem("use"),
                    UItem("det", editor=EnumEditor(name="detectors")),
                    UItem("mode"),
                ),
                VGroup(
                    direct_grp,
                    scale_grp,
                    transform_grp,
                ),
            )
        )
        return v

    def tostr(self):
        if self.mode == "Direct":
            return f"{self.mode}  {self.det}:{self.value}({self.error})"
            # return self.value and self.error
        elif self.mode == "Scale":
            return f"{self.mode}  {self.det}:{self.scaling_value}"
        elif self.mode == "Transform":
            return f"{self.mode}  {self.det}:{self.transform_variable}({self.transform_coefficients})"


class BulkOptions(HasTraits):
    ic_factors = List
    detectors = List

    aliquot = Int
    step = StepStr
    comment = Str

    sync_sample_enabled = Bool

    @property
    def icfactor_message(self):
        return [ic.tostr() for ic in self.ic_factors if ic.enabled]

    def traits_view(self):
        icgrp = BorderVGroup(
            UItem(
                "ic_factors",
                editor=ListEditor(
                    mutable=False, style="custom", editor=InstanceEditor()
                ),
            ),
            label="IC Factors",
        )

        runid_grp = BorderVGroup(HGroup(Item("aliquot"), Item("step")), label="RunID")
        sample_grp = BorderVGroup(
            Item(
                "sync_sample_enabled",
                label="Sync Sample MetaData",
                tooltip="Sync analysis sample metadata to the database",
            ),
            label="Sample",
        )
        analysis_grp = BorderVGroup(Item("comment"), label="Analysis")
        v = okcancel_view(
            VGroup(
                icgrp,
                runid_grp,
                sample_grp,
                analysis_grp,
            ),
            title="Bulk Edit Options",
        )
        return v

    def _ic_factors_default(self):
        return [
            ICFactor(detectors=self.detectors),
            ICFactor(detectors=self.detectors),
            ICFactor(detectors=self.detectors),
        ]


class BulkEditNode(BaseDVCNode):
    options_klass = BulkOptions
    name = "Bulk Edit"

    def pre_run(self, state, configure=True):
        if state.unknowns:
            dets = list(
                {iso.detector for ai in state.unknowns for iso in ai.itervalues()}
            )
            self.options.detectors = dets

        return super(BulkEditNode, self).pre_run(state, configure=configure)

    def run(self, state):
        ans = state.unknowns

        icfs = [ic_factor for ic_factor in self.options.ic_factors if ic_factor.enabled]
        author = self.dvc.get_author()
        if icfs:
            for ai in ans:
                self._bulk_ic_factor(ai, icfs)

            self.dvc.update_analyses(
                ans,
                "icfactors",
                "<ICFactor> bulk edit {}".format(self.options.icfactor_message),
                author,
            )

        if self.options.aliquot or self.options.step:
            if not author:
                author = self.dvc.get_author()

            paths = {}
            for ai in ans:
                expid, ps = self._bulk_runid(
                    ai, self.options.aliquot, self.options.step
                )
                if expid in paths:
                    pp = paths[expid]
                    pp.extend(ps)
                else:
                    pp = ps

                paths[expid] = pp

            for expid, ps in paths.items():
                if self.dvc.repository_add_paths(expid, ps):
                    self.dvc.repository_commit(expid, "<EDIT> RunID", author)

        if self.options.sync_sample_enabled or self.options.comment:
            if not author:
                author = self.dvc.get_author()

            message = "<EDIT>"
            if self.options.sync_sample_enabled:
                message = f"{message} Sync Sample MetaData"

            for repo, ais in groupby_repo(ans):
                ais = list(ais)
                self.dvc.pull_repository(repo)
                ps = []
                for identifier, aais in groupby_key(ais, attrgetter("identifier")):
                    ps.extend(self.dvc.analyses_db_sync(identifier, aais, repo))

                if self.options.comment:
                    message = f"{message} {self.options.comment}"
                    dbais = self.dvc.db.get_analyses_uuid([ai.uuid for ai in ais])
                    for dbai, ai in zip(dbais, ais):
                        ai.comment = self.options.comment
                        p = self.dvc.edit_comment(ai.uuid, repo, self.options.comment)
                        ps.append(p)

                if self.dvc.repository_add_paths(repo, ps):
                    self.dvc.repository_commit(repo, message, author)

    def _bulk_runid(self, ai, aliquot, step):
        if not aliquot:
            aliquot = ai.aliquot
        if not step:
            step = ai.step

        self.dvc.db.modify_aliquot_step(ai.uuid, aliquot, alpha_to_int(step))

        def modify_meta(p):
            jd = dvc_load(p)

            jd["aliquot"] = aliquot
            jd["increment"] = alpha_to_int(step)

            dvc_dump(jd, p)

        ps = []
        repo_id = ai.repository_identifier
        sp = analysis_path(("", ai.record_id), repo_id)
        if sp:
            modify_meta(sp)
            ps.append(sp)
            # using runid path name
            new_runid = make_runid(ai.identifier, aliquot, step)
            for m in NPATH_MODIFIERS:
                sp = analysis_path(("", ai.record_id), repo_id, modifier=m)
                dp = analysis_path(("", new_runid), repo_id, modifier=m, mode="w")
                if sp and os.path.isfile(sp):
                    if os.path.isfile(dp) and m != "extraction":
                        continue
                    ps.append(sp)
                    ps.append(dp)
                    shutil.move(sp, dp)
        else:
            # using uuid path name
            # only need to modify metadata file
            sp = analysis_path(ai, repo_id)
            modify_meta(sp, aliquot, step)
            ps.append(sp)

        return repo_id, ps

    def _bulk_ic_factor(self, ai, icfs):
        keys, fits = [], []
        for ic_factor in icfs:
            keys.append(ic_factor.det)
            fits.append("bulk_edit")

            if ic_factor.mode == "Scale":
                ic = ai.calculate_transform_ic_factor(
                    ic_factor.det,
                    "ICFactor",
                    [ic_factor.scaling_value, 0],
                    tag=f"{ic_factor.det} IC",
                )
            elif ic_factor == "Transform":
                ic = ai.calculate_transform_ic_factor(
                    ic_factor.det,
                    ic_factor.transform_variable,
                    [float(c) for c in ic_factor.transform_coefficients.split(",")],
                    tag=f"{ic_factor.det} IC",
                )
            else:
                # print('ic', ic_factor.det, ic_factor.value, ic_factor.error)
                ic = ai.set_temporary_ic_factor(
                    ic_factor.num,
                    ic_factor.det,
                    ic_factor.value,
                    ic_factor.error,
                    tag="{} IC".format(ic_factor.det),
                )
            for iso in ai.get_isotopes_for_detector(ic_factor.det):
                iso.ic_factor = ic

        ai.dump_icfactors(keys, fits, reviewed=True)


class RevertHistoryNode(BaseDVCNode):
    name = "Revert History"
    configurable = False

    def run(self, state):
        ans = state.unknowns
        for repo, ais in groupby_repo(ans):
            self.dvc.rollback_to_collection(ais, repo)


if __name__ == "__main__":
    b = BulkOptions()
    b.detectors = ["H1", "AX", "CDD"]
    b.configure_traits()
# ============= EOF =============================================
