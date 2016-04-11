# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
# ============= standard library imports ========================
# ============= local library imports  ==========================


class no_update(object):
    _model = None

    def __init__(self, model, fire_update_needed=True):
        self._model = model
        self._fire_update_needed = fire_update_needed

    def __enter__(self):
        if self._model:
            self._model._no_update = True

    def __exit__(self, _type, value, _traceback):
        if self._model:
            self._model._no_update = False
            if self._fire_update_needed:
                if hasattr(self._model, 'update_needed'):
                    self._model.update_needed = True

# ============= EOF =============================================
