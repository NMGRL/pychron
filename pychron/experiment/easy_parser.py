#===============================================================================
# Copyright 2013 Jake Ross
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

#============= enthought library imports =======================
import os
from traits.api import List, Int

#============= standard library imports ========================
#============= local library imports  ==========================
import yaml
from pychron.paths import paths
from pychron.core.helpers.filetools import add_extension
from pychron.loggable import Loggable


doc_mapping = ['setup', 'import', 'iso_fits', 'blanks', 'disc', 'figures', 'tables']

class EasyParser(Loggable):
    _docs = List
    _ndocs = Int

    def __init__(self, name=None, *args, **kw):
        super(EasyParser, self).__init__(*args, **kw)
        # if name is None:
        #     name = 'minna_bluff_prj3'

        # name = add_extension(name, '.yaml')
        # p = os.path.join(paths., name)
        p='/Users/ross/Programming/git/dissertation/data/minnabluff/preceeding_blank_unknowns.yaml'

        if os.path.isfile(p):
            with open(p, 'r') as fp:
                md = yaml.load_all(fp)
                self._docs = list(md)
                self._ndocs = len(self._docs)
        else:
            self.warning_dialog('Invalid EasyParser file. {}'.format(self._path))

    def doc(self, idx):

        if isinstance(idx, str):
            try:
                idx = doc_mapping.index(idx)
            except ValueError:
                self.warning_dialog('Invalid Document index {}. ndocs={}'.format(idx, ','.join(doc_mapping)))
                return

        print self._docs, idx
        try:
            return self._docs[idx]
        except IndexError:
            self.warning_dialog('Invalid Document index {}. ndocs={}'.format(idx, self._ndocs))

#============= EOF =============================================

