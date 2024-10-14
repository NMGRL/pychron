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

from traits.api import HasTraits, List, Any, Str
from traitsui.api import UItem, TabularEditor, EnumEditor, VGroup

from pychron.core.helpers.iterfuncs import groupby_repo
from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.dvc import HISTORY_PATHS, HISTORY_TAGS
from pychron.git_archive.utils import get_commits
from pychron.git_archive.views import CommitAdapter
from pychron.pipeline.nodes.data import BaseDVCNode


class CommitSelector(HasTraits):
    commits = List
    selected = Any
    repo = Any
    branches = List
    branch = Str
    paths = List
    greps = List

    def __init__(self, repo, unks, *args, **kw):
        super(CommitSelector, self).__init__(*args, **kw)
        self.repo = repo
        self.set_paths(unks)
        self.load_branches()
        self.load_commits()

    def _branch_changed(self):
        self.load_commits()

    def load_branches(self):
        self.branches = self.repo.get_branch_names()
        b = self.repo.get_active_branch()
        self.branch = b

    def set_paths(self, unks):
        self.paths = [a.make_path(p) for a in unks for p in HISTORY_PATHS]
        greps = ["--grep=^<{}>".format(t) for t in HISTORY_TAGS]
        self.greps = greps

    def load_commits(self):
        cs = get_commits(self.repo.path, self.branch, self.paths, "", greps=self.greps)
        self.commits = cs

    def traits_view(self):
        v = okcancel_view(
            VGroup(
                UItem("branch", editor=EnumEditor(name="branches")),
                UItem(
                    "commits",
                    editor=TabularEditor(
                        adapter=CommitAdapter(), editable=False, selected="selected"
                    ),
                ),
            ),
            title="Change Selector",
            height=600,
            width=700,
        )
        return v


class DVCHistoryNode(BaseDVCNode):
    options_klass = CommitSelector
    name = "History Select"

    def pre_run(self, state, configure=True):
        unks = state.unknowns

        state.selected_commits = {}
        for repo, unks in groupby_repo(unks):
            # cs = get_commits(repo, , None, '')()
            repo = self.dvc.get_repository(repo)
            cv = CommitSelector(repo, unks)

            info = cv.edit_traits(kind="livemodal")
            if not info.result:
                return

            if not cv.selected:
                return
            state.selected_commits[repo.name] = cv.selected.hexsha
        return True

    def run(self, state):
        unks = state.unknowns
        for repo, ans in groupby_repo(unks):
            repo = self.dvc.get_repository(repo)
            # abranch = repo.get_current_branch()

            try:
                # repo.create_branch(
                #     branchname, state.selected_commits[repo.name], inform=False
                # )

                ps = [an.make_path(p) for an in ans for p in HISTORY_PATHS]

                repo.checkout(state.selected_commits[repo.name], "--", ps)
                pans = self.dvc.make_analyses(
                    list(ans),
                    reload=True,
                    use_cached=False,
                    sync_repo=False,
                    use_flux_histories=False,
                )
                if pans:
                    # only allow one history group for right now.
                    # in the future add a history_group_id
                    # analyses are then partitioned by group_id then history_group_id
                    for unk in pans:
                        unk.group_id = 1
                        unk.history_id = 1

                    unks.extend(pans)
            except BaseException:
                pass
            finally:
                repo.restore_branch(ps)
                # branch = repo.get_branch(abranch)
                # branch.checkout()
                # repo.delete_branch(branchname)


# ============= EOF =============================================
