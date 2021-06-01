# ===============================================================================
# Copyright 2021 ross
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
from traits.api import Callable


from pychron.canvas.canvas2D.scene.primitives.base import QPrimitive
from pychron.canvas.canvas2D.scene.primitives.primitives import ValueLabel


class Widget(ValueLabel):
    _update_function = Callable

    def __init__(self, func, *args, **kw):
        super(Widget, self).__init__(*args, **kw)
        self._update_function = func

    def update(self):
        v = self._update_function()
        if isinstance(v, float):
            v = '{:0.3f}'.format(v)

        self.value = v
# ============= EOF =============================================
