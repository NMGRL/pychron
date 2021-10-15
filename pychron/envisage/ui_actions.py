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
from pyface.tasks.action.task_action import TaskAction
from traits.has_traits import MetaHasTraits
from traitsui.menu import Action


class NameMeta(MetaHasTraits):
    def __new__(cls, name, bases, d):
        if "name" in d:
            name = d["name"]
            if name.endswith("..."):
                name = name[:-3]
            d["dname"] = name

        if "description" in d:
            d["ddescription"] = d["description"]

        return super().__new__(cls, name, bases, d)


class UIAction(Action, metaclass=NameMeta):
    pass


class UITaskAction(TaskAction, metaclass=NameMeta):
    pass

# ============= EOF =============================================
