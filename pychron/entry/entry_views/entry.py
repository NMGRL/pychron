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
from traits.api import HasTraits, Button, Any, Instance
from traitsui.api import View, Item
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.loggable import Loggable


class BaseEntry(Loggable):
    db = Instance('pychron.database.adapters.isotope_adapter.IsotopeAdapter')

    def do(self):
        return self._add_loop()

    def _add_loop(self):
        while 1:
            info = self.edit_traits()
            if info.result:
                db = self.db
                with db.session_ctx():
                    if self._add_item(db):
                        return True
            else:
                return False

    def _add_item(self, db):
        raise NotImplementedError

    def _new_view(self, *args, **kw):
        for a, v in (('buttons', ['OK', 'Cancel']),
                     ('resizable', True),
                     ('kind', 'livemodal')):
            if not kw.has_key(a):
                kw[a] = v

        v = View(*args, **kw)
        return v

# ============= EOF =============================================



