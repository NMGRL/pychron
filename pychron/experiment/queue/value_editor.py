# ===============================================================================
# Copyright 2019 ross
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
import re

from traits.api import Str, List, Float, BaseStr, HasTraits
from traitsui.api import HGroup, UItem, EnumEditor, Item, TextEditor

from pychron.core.helpers.traitsui_shortcuts import okcancel_view
from pychron.loggable import Loggable

REPLACE_REGEX = re.compile(r"\d+\.?\d?")
AUGEMENT_REGEX = re.compile(r"(?P<operand>[\+\*\-])\=(?P<value>\d+\.?\d?)")


class ValueStr(BaseStr):
    def validate(self, obj, name, value):
        if not value or REPLACE_REGEX.match(value) or AUGEMENT_REGEX.match(value):
            return value
        else:
            self.error(obj, name, value)


MAPPING = {
    "Extract Value": "extract_value",
    "Cleanup": "cleanup",
    "Duration": "duration",
    "Beam": "beam_diameter",
    "Ramp": "ramp_duration",
}


class ValueEditor(Loggable):
    parameter = Str
    parameters = List
    value = ValueStr

    def __init__(self, queue, *args, **kw):
        self._queue = queue
        super(ValueEditor, self).__init__(*args, **kw)

    def _value_changed(self, new):
        if new == "":
            return

        m = AUGEMENT_REGEX.match(new)

        if m:
            operand = m.group("operand")
            a = float(m.group("value"))
            if operand == "+":

                def func(v):
                    return v + a

            elif operand == "-":

                def func(v):
                    return v - a

            else:

                def func(v):
                    return v * a

        else:

            def func(v):
                return float(new)

        param = MAPPING.get(self.parameter)
        for s in self._queue.selected:
            v = getattr(s, param)
            if not v:
                v = 0
            nv = func(v)
            setattr(s, param, nv)

        self._queue.refresh_table_needed = True

    def _parameters_default(self):
        return sorted(MAPPING.keys())

    def traits_view(self):
        v = okcancel_view(
            HGroup(
                UItem("parameter", editor=EnumEditor(name="parameters")),
                Item(
                    "value",
                    editor=TextEditor(enter_set=True, auto_set=False),
                    tooltip="""1. Enter a number to modify all values to entered number. e.g 10
2. Use +=N to add N to all values. e.g +=10 adds 10 to all values. -= and *= also valid""",
                ),
            ),
            title="Value Editor",
            buttons=[
                "OK",
            ],
            default_button=None,
        )
        return v


if __name__ == "__main__":

    class I(HasTraits):
        extract_value = Float(1)
        duration = Float(2)
        cleanup = Float(3)

    class Q:
        selected = List

    q = Q()
    q.selected = [I(cleanup=i) for i in range(3)]

    ve = ValueEditor(q)
    ve.configure_traits()
# ============= EOF =============================================
