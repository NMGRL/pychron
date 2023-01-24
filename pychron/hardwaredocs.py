# ===============================================================================
# Copyright 2023 ross
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

import sys, os
import yaml

root = os.path.dirname(os.path.dirname(__file__))
sys.path.append(root)

from pychron.hardware.actuators import PACKAGES
from pychron.hardware import HW_PACKAGE_MAP


def extract_doc(mod, cf):
    classname = cf.__name__
    name = classname
    rdoc = cf.__doc__
    doc = ""
    description = ""
    if rdoc:
        active = False
        lines = rdoc.split("\n")
        for i, line in enumerate(lines):
            if line.strip() == ":::":
                active = True
                break

        if active:
            doc = "\n".join(lines[i + 1 :])
            try:
                ydoc = yaml.load(doc, Loader=yaml.SafeLoader)
                description = ydoc.pop("description", description)
                name = ydoc.pop("name", classname)
                doc = yaml.dump(ydoc)
            except yaml.YamlError as e:
                print("asdf", e)

    return f"""{name}
==========================

<p>
{description}
</p>

<b>Module:</b> {mod}<br>
<b>Class:</b> {classname}

```yaml
{doc}
```
"""


def assemble_docs():
    contents = []

    for klass, package in sorted(list(HW_PACKAGE_MAP.items()) + list(PACKAGES.items())):
        print(klass, package)

        # package = HW_PACKAGE_MAP[klass]
        try:
            m = __import__(package, globals(), locals(), [klass])
        except ModuleNotFoundError as e:
            print("No module", e)
            continue

        try:
            class_factory = getattr(m, klass)
        except AttributeError as e:
            print("No klass", e)
            if klass == "Eurotherm":
                print(dir(m))
            continue
        print("built", klass)
        description_doc = extract_doc(package, class_factory)
        contents.append(description_doc)

    content = "# Available Hardware Drivers\n".join(contents)
    pname = os.environ.get("PNAME", "hardwaredocs.md")
    with open(os.path.join(root, "pychron", pname), "w") as wfile:
        wfile.write(content)


if __name__ == "__main__":
    assemble_docs()

# ============= EOF =============================================
