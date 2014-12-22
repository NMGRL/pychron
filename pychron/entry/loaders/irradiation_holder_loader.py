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
from pyface.file_dialog import FileDialog
# ============= standard library imports ========================
import os
# ============= local library imports  ==========================
from pychron.database.defaults import load_irradiation_map
from pychron.loggable import Loggable
from pychron.paths import paths


class IrradiationHolderLoader(Loggable):
    def do_import(self, db):
        path = self._get_holder_path()
        if path:
            self.debug('doing irradiation holder import')
            overwrite_geometry = True
            name = os.path.splitext(os.path.basename(path))[0]
            msg='Added'
            with db.session_ctx():
                dbh = db.get_irradiation_holder(name)
                if dbh:
                    msg='Updated'
                load_irradiation_map(db, path, name, overwrite_geometry)

                self.information_dialog('{} Irradiation Holder "{}"'.format(msg, name))

    def _get_holder_path(self):
        dlg=FileDialog(default_directory=paths.irradiation_tray_maps_dir,
                       wildcard='*.txt')
        if dlg.open():
            if dlg.path:
                return dlg.path
# ============= EOF =============================================



