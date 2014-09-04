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
from pychron.core.ui import set_qt
set_qt()
# ============= enthought library imports =======================
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.git_archive.history import GitArchiveHistory, GitArchiveHistoryView


class LocalMFTableHistory(GitArchiveHistory):
    pass


class LocalMFTableHistoryView(GitArchiveHistoryView):
    pass

if __name__ == '__main__':
    r = '/Users/ross/Sandbox/gitarchive'
    gh = GitArchiveHistory(r, '/Users/ross/Sandbox/ga_test.txt')

    gh.load_history('ga_test.txt')
    ghv = GitArchiveHistoryView(model=gh)
    ghv.configure_traits(kind='livemodal')
#============= EOF =============================================



