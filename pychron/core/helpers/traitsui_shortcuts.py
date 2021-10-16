# ===============================================================================
# Copyright 2012 Jake Ross
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
from os import environ

from traitsui.api import Item, ListEditor, InstanceEditor, View, VGroup, VFold as _VFold
from traitsui.menu import OKButton

# ============= standard library imports ========================
# ============= local library imports  ==========================

if not environ.get("VFOLD_ENABLED", True):
    VFold = VGroup
else:
    VFold = _VFold


def instance_item(name, **kw):
    return Item(name, style="custom", show_label=False, **kw)


def listeditor(name, **kw):
    return Item(
        name,
        show_label=False,
        editor=ListEditor(mutable=False, style="custom", editor=InstanceEditor()),
        **kw
    )


def okcancel_view(*args, **kw):
    if "kind" not in kw:
        kw["kind"] = "livemodal"
    if "default_button" not in kw:
        kw["default_button"] = OKButton
    if "resizable" not in kw:
        kw["resizable"] = True
    if "buttons" not in kw:
        kw["buttons"] = ["OK", "Cancel"]

    return View(*args, **kw)


def rfloatitem(*args, **kw):
    kw["style"] = "readonly"
    return floatitem(*args, **kw)


def floatitem(name, sigfigs=3, **kw):
    return Item(name, format_str="%0.{}f".format(sigfigs), **kw)


# ============= EOF =============================================
