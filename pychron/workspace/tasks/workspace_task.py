# ===============================================================================
# Copyright 2014 Jake Ross
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
import os

from pyface.tasks.action.schema import SToolBar
from traits.api import Instance

#============= standard library imports ========================
#============= local library imports  ==========================
import yaml
from pychron.core.progress import progress_iterator
from pychron.paths import paths
from pychron.processing.export.yaml_analysis_exporter import YamlAnalysisExporter
from pychron.processing.tasks.browser.browser_task import BaseBrowserTask
from pychron.workspace.tasks.actions import NewWorkspaceAction, OpenWorkspaceAction, CheckoutAnalysesAction, \
    AddBranchAction, TestModificationAction, TagBranchAction, PullAction, PushAction, CommitChangesAction
from pychron.workspace.tasks.panes import WorkspaceCentralPane, WorkspaceControlPane
from pychron.workspace.tasks.views import ChooseReheckoutAnalysesView
from pychron.workspace.workspace_manager import ArArWorkspaceManager


class WorkspaceTask(BaseBrowserTask):

    tool_bars = [SToolBar(NewWorkspaceAction(),
                          OpenWorkspaceAction()),
                 SToolBar(CheckoutAnalysesAction(),
                          AddBranchAction(),
                          TagBranchAction(),
                          TestModificationAction()),
                 SToolBar(PullAction(),
                          PushAction(),
                          CommitChangesAction())]

    workspace = Instance(ArArWorkspaceManager, ())

    def commit_changes(self):
        self.debug('merging develop into master')
        self.workspace.merge('develop', 'master')

    def pull(self):
        self.debug('pull')

    def push(self):
        self.debug('push')

    def tag_branch(self):
        from pychron.workspace.tasks.views import NewTagView
        b = self.workspace.get_current_branch()
        self.debug('tag branch={}'.format(b))
        nt = NewTagView(branch=b)
        info = nt.edit_traits()
        if info.result:
            self.info('tagging {} as {}'.format(b, nt.tag_name))
            self.workspace.tag_branch(nt.tag_name)

    def test_modification(self):
        import random
        p=os.path.join(self.workspace.path, '23446-01.yaml')
        with open(p, 'w') as fp:
            fp.write(yaml.dump({'foo':random.random()}))

        self.workspace.modify_analysis(p)

    def add_branch(self):
        from pychron.workspace.tasks.views import NewBranchView
        nb = NewBranchView()
        info = nb.edit_traits()
        if info.result:
            self.workspace.create_branch(nb.name)

    def checkout_analyses(self):
        if not self.workspace.path:
            return

        self.debug('checking out analyses')
        ans = self.analysis_table.analyses

        #check for existing
        #ask user to selected which files to overwrite
        existing =self.workspace.find_existing(['{}.yaml'.format(ai.record_id) for ai in ans])
        recheckout=None
        if existing:
            self.debug('Analyses exist in workspace')
            ce = ChooseReheckoutAnalysesView(existing)
            info=ce.edit_traits()
            if info.result:
                recheckout = ce.get_analyses_to_checkout()
            else:
                return

        if recheckout:
            recheckout = [ai for ai in ans if ai.record_id in recheckout]
        ans = [ai for ai in ans if not ai.record_id in existing]

        if not ans and not recheckout:
            self.info('no analyses to checkout')
            return

        self.workspace.checkout_branch('master')
        if ans:
            self.debug('checkout {}'.format(','.join([ai.record_id for ai in ans])))
            self._checkout_analyses(ans)
        if recheckout:
            self.debug('recheckout {}'.format(','.join([ai.record_id for ai in recheckout])))
            self._checkout_analyses(recheckout, 'Recheckout')

        self.workspace.merge('master', 'develop')
        self.workspace.checkout_branch('develop')

    def _checkout_analyses(self, ans, msg='Added'):
        #make dbanalyses
        ans = self.manager.make_analyses(ans, unpack=True, calculate_age=True)

        #export to yaml files
        exp=YamlAnalysisExporter()
        def func(ai, prog, i, n):
            exp.add(ai)
            p= os.path.join(self.workspace.path,'{}.yaml'.format(ai.record_id))
            exp.destination.destination = p

            exp.export()
            # timethis(exp.export, msg='export')
            exp.clear()

            #update manifest
            self.workspace.add_to_manifest(p)
            # timethis(self.workspace.add_to_manifest, args=(p,), msg='a')

            #add to repositiory
            self.workspace.add_analysis(p, commit=False)
            # timethis(self.workspace.add_analysis, args=(p,),
            #          kwargs={'commit':False},
            #          msg='add to git')
            if prog:
                prog.change_message('{} {} to workspace'.format(msg, ai.record_id))

        progress_iterator(ans, func, threshold=1)
        self.workspace.add_manifest_to_index()
        self.workspace.commit('{} Analyses {} to {}'.format(msg, ans[0].record_id,
                                                               ans[-1].record_id))
    def new_workspace(self):
        self.debug('new workspace')

    def open_workspace(self):
        self.debug('open workspace')
        p='/Users/ross/Pychrondata_dev/data/workspaces/test'
        if not os.path.isdir(p):
            p = self.open_directory_dialog(default_directory=paths.workspace_root_dir)

        if p:
            self.workspace.open_repo(p)

    def create_central_pane(self):
        return WorkspaceCentralPane(model=self.workspace)

    def create_dock_panes(self):
        return [WorkspaceControlPane(),
                self._create_browser_pane()]
#============= EOF =============================================


