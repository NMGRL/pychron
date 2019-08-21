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
from traits.api import HasTraits, List
from traitsui.api import View, UItem

from pychron.core.ui.dag_editor import GitDAGEditor
from pychron.git_archive.repo_manager import GitRepoManager
from pychron.git_archive.views import CommitFactory


class DAGViewer(HasTraits):
    commits = List

    def load(self):

        repo = GitRepoManager()
        repo.open_repo('gitlogtest', '/Users/ross/Sandbox')
        cs = repo.get_topology(branch='---', include_graph=False)
        self.commits = [CommitFactory.new(log_entry=ci) for ci in reversed(cs.split('\n'))]
        for ci in self.commits:
            print(ci.oid, id(ci), 'parents={}, children={}'.format(','.join([str(id(p)) for p in ci.parents]),
                                                           ','.join([str(id(p)) for p in ci.children])))

    def traits_view(self):
        v = View(UItem('commits', editor=GitDAGEditor()),
                 resizable=True, width=200, height=300)
        return v


if __name__ == '__main__':
    g = DAGViewer()
    g.load()
    g.configure_traits()



# ============= EOF =============================================
