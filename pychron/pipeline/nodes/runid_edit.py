# ===============================================================================
# Copyright 2020 ross
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

from pyface.confirmation_dialog import confirm
from pyface.constant import YES
from pyface.message_dialog import warning
from traits.api import List, HasTraits, Str, Int
from traitsui.api import UItem, TableEditor
from traitsui.table_column import ObjectColumn

from pychron.core.helpers.iterfuncs import groupby_repo
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.experiment.utilities.runid import make_runid
from pychron.paths import paths
from pychron.pipeline.nodes.data import BaseDVCNode


class RunIDEditItem(HasTraits):
    src_record_id = Str
    dest_identifier = Str
    dest_aliquot = Int
    dest_step = Str
    uuid = Str

    def __init__(self, a, *args, **kw):
        super(RunIDEditItem, self).__init__(*args, **kw)
        self.src_record_id = a.record_id
        self.dest_identifier = a.identifier
        self.dest_aliquot = a.aliquot
        self.dest_step = a.step
        self.repository_identifier = a.repository_identifier
        self.uuid = a.uuid

    @property
    def dest_record_id(self):
        return make_runid(self.dest_identifier, self.dest_aliquot, self.dest_step)


class RunIDEditNode(BaseDVCNode):
    items = List
    name = "RunID Edit"

    def traits_view(self):
        cols = [
            ObjectColumn(name="src_record_id"),
            ObjectColumn(name="dest_identifier"),
            ObjectColumn(name="dest_aliquot"),
            ObjectColumn(name="dest_step"),
        ]

        return okcancel_view(
            UItem("items", editor=TableEditor(columns=cols)),
            width=500,
            height=700,
            title="RunID Edit",
        )

    def _pre_run_hook(self, state):
        self.items = [RunIDEditItem(a) for a in state.unknowns]

    def run(self, state):
        if (
            confirm(
                None,
                "This is only for advanced users. Serious unintended consequences may occur if not used "
                "properly. Please do not use unless you are capable of manually fixing database/repository "
                "issues. \n\n Are you sure you want to continue",
            )
            != YES
        ):
            return

        for repo, items in groupby_repo(self.items):
            pss = []
            for item in items:
                ps = self.dvc.fix_identifier(
                    item.uuid,
                    item.src_record_id,
                    item.dest_record_id,
                    repo,
                    item.dest_identifier,
                    item.dest_aliquot,
                    item.dest_step,
                )
                pss.extend(ps)

            self.dvc.commit()

            base = os.path.join(paths.repository_dataset_dir, repo)
            temp = os.path.join(base, "temp")

            crepo = self.dvc.get_repository(repo)
            for p in pss:
                np = p.replace(temp, base)
                shutil.move(p, np)
                crepo.add(np, commit=False)

            # add deleted files
            # deletes = crepo.get_local_changes(change_type=('D',))
            # crepo.index.add(deletes)

            # crepo.commit('edit runids')
            # take all the temp files and move them into the repository
            # overriding existing files where applicable

            # add all the temps to the git index
            # commit the changes

        warning(
            None,
            "This process is not fully complete. You need to manual add/commit modified files",
        )


# ============= EOF =============================================
