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
from __future__ import absolute_import

from traits.api import Bool, Any, List, Str
from traitsui.api import View

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.column_sorter_mixin import ColumnSorterMixin


class BaseNode(ColumnSorterMixin):
    name = 'Base'
    enabled = Bool(True)
    visited = Bool(False)
    skip_configure = Bool(False)
    options_klass = None
    options = Any
    auto_configure = Bool(True)
    configurable = Bool(True)

    active = Bool(False)
    # metadata = Event
    _manual_configured = Bool(False)

    # analyses = List
    unknowns = List
    references = List
    required = List
    index = -1

    skip_meaning = Str
    use_state_unknowns = True
    use_state_references = True

    def resume(self, state):
        pass

    def clear_data(self):
        self.unknowns = []
        self.references = []

    def reset(self):
        self.visited = False
        self._manual_configured = False
        self.active = False

    def pre_load(self, nodedict):
        for k, v in nodedict.items():
            if hasattr(self, k):
                setattr(self, k, v)

    def load(self, nodedict):
        pass

    def finish_load(self):
        pass

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def _pre_run_hook(self, state):
        pass

    def pre_run(self, state, configure=True):
        self._pre_run_hook(state)

        if not self.auto_configure:
            return True

        if self._manual_configured:
            return True

        if state.unknowns:
            self.unknowns = state.unknowns
        if state.references:
            self.references = state.references

        if configure:
            if self.skip_configure:
                return True

            if self.configure(refresh=False, pre_run=True):
                return True
            else:
                state.canceled = True
        else:
            return True

    def run(self, state):
        raise NotImplementedError(self.__class__.__name__)

    def post_run(self, engine, state):
        pass

    def refresh(self):
        pass

    def configure(self, pre_run=False, **kw):
        if not pre_run:
            self._manual_configured = True

        return self._configure(**kw)

    def _configure(self, obj=None, **kw):
        if self.configurable:
            if obj is None:
                if self.options_klass:
                    obj = self.options
                else:
                    obj = self

            self._configure_hook()
            info = obj.edit_traits(kind='livemodal')
            if info.result:
                self._finish_configure()
                self.refresh()
                return True
        else:
            return True

    def _configure_hook(self):
        pass

    def _finish_configure(self):
        pass

    def to_template(self):
        d = {'klass': self.__class__.__name__}
        self._to_template(d)

        return d

    def _options_factory(self):
        if self.options_klass:
            return self.options_klass()

    def _options_default(self):
        return self._options_factory()

    def _to_template(self, d):
        pass
        # return []

    def _view_factory(self, *items, **kw):
        if 'title' not in kw:
            kw['title'] = 'Configure {}'.format(self.name)

        return View(buttons=['OK', 'Cancel'],
                    kind='livemodal', *items, **kw)

    def __str__(self):
        return '{}<{}>'.format(self.name, self.__class__.__name__)


class SortableNode(BaseNode, ColumnSorterMixin):
    pass
# ============= EOF =============================================
