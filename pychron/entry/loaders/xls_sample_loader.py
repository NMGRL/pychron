# ===============================================================================
# Copyright 2015 Jake Ross
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
from traits.api import HasTraits, Str, Int, Bool, Any, Float, Property, on_trait_change
from traitsui.api import View, UItem, Item, HGroup, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.xls.xls_parser import XLSParser
from pychron.loggable import Loggable


class XLSSampleLoader(Loggable):
    def do_loading(self, manager, path, dry=True):
        if not os.path.isfile(path):
            self.warning('No file located at {}'.format(path))

        # path to sample_file.xls
        p = ''

        xp = XLSParser()
        xp.load(path, header_idx=2)

        overwrite_meta = True
        overwrite_alt_name = True
        add_samples = True

        db = manager.db
        progress = manager.open_progress(xp.nrows)

        with db.session_ctx(commit=not dry):
            keys = ('sample', 'project', 'material')
            for args in xp.itervalues(keys=keys):
                sample, project, material = args['sample'], args['project'], args['material']

                progress.change_message('Setting sample {}'.format(sample))

                dbsample = db.get_sample(sample, project, material, verbose=False)
                if not dbsample:
                    if add_samples:
                        dbsample = db.add_sample(sample, project, material)

            progress.close()

# ============= EOF =============================================



