#===============================================================================
# Copyright 2014 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================
from pychron.core.helpers.logger_setup import logging_setup
from pychron.core.ui import set_qt

set_qt()
#============= enthought library imports =======================
import yaml
#============= standard library imports ========================
import os
#============= local library imports  ==========================

from pychron.workspace.index import IndexAdapter, Base, AnalysisIndex
from pychron.workspace.workspace_manager import WorkspaceManager

logging_setup('wm')




if __name__ == '__main__':
    root = os.path.expanduser('~')
    root = os.path.join(root, 'Sandbox', 'workspace')
    wm = WorkspaceManager()
    wm.create_repo('test', root, None)

    idx = IndexAdapter(path=os.path.join(root, 'index.db'),
                       schema=AnalysisIndex)
    idx.connect()

    idx.create_all(Base.metadata)

    wm.index_db = idx

    tpath = os.path.join(root, 'record.yaml')
    wm.add_record(tpath, identifier='12345', aliquot=1)

    tpath = os.path.join(root, 'record2.yaml')
    wm.add_record(tpath, identifier='12345', aliquot=2)

    mpath = os.path.join(root, 'test', 'record2.yaml')

    with open(mpath, 'w') as fp:
        d = dict(age=10, error=0.1)
        yaml.dump(d, fp, default_flow_style=False)

    wm.modify_record(mpath)


    # print wm.schema_diff(('age', 'error'))
    # wm.commit_modification()
    # print wm.schema_diff(('age', 'error'))



#============= EOF =============================================



