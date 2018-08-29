# ===============================================================================
# Copyright 2018 ross
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

import six
from traits.api import Bool
from traitsui.editors import CheckListEditor as tCheckListEditor
from traitsui.qt4.check_list_editor import CustomEditor, parse_value


class _CheckListEditor(CustomEditor):
    def list_updated(self, values):
        if self.factory.capitalize:
            super(_CheckListEditor, self).list_updated(values)

        else:
            # sv = self.string_value
            if (len(values) > 0) and isinstance(values[0], six.string_types):
                values = [(x, x) for x in values]

            self.values = valid_values = [x[0] for x in values]
            self.names = [x[1] for x in values]

            # Make sure the current value is still legal:
            modified = False
            cur_value = parse_value(self.value)
            for i in range(len(cur_value) - 1, -1, -1):
                if cur_value[i] not in valid_values:
                    try:
                        del cur_value[i]
                        modified = True
                    except TypeError as e:
                        pass
                        # logger.warn('Unable to remove non-current value [%s] from '
                        #             'values %s', cur_value[i], values)
            if modified:
                if isinstance(self.value, six.string_types):
                    cur_value = ','.join(cur_value)
                self.value = cur_value

            self.rebuild_editor()


class CheckListEditor(tCheckListEditor):
    capitalize = Bool(True)

    def _get_custom_editor_class(self):
        """ Returns the editor class to use for "custom" style views.
        The default implementation tries to import the CustomEditor class in the
        editor file in the backend package, and if such a class is not to found
        it returns simple_editor_class.

        """
        return _CheckListEditor
# ============= EOF =============================================
