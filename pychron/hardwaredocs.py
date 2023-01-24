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

p = os.path.dirname(os.path.dirname(__file__))
sys.path.append(p)


from pychron.hardware import HW_PACKAGE_MAP

import sys


def extract_doc(cf):
    name = cf.__name__
    rdoc = cf.__doc__
    doc = ""
    if rdoc:
        active = False
        lines = rdoc.split("\n")
        for i, line in enumerate(lines):
            if line.strip() == ":::":
                active = True
                break

        if active:
            doc = "\n".join(lines[i + 1 :])

    return f"""{name}
==========================
{doc}
    """


def assemble_docs():
    contents = []
    for klass, package in HW_PACKAGE_MAP.items():
        # print(klass, package)

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
            continue

        description_doc = extract_doc(class_factory)
        contents.append(description_doc)

    content = "\n".join(contents)
    with open("./hardwaredocs.md", "w") as wfile:
        wfile.write(content)


if __name__ == "__main__":
    assemble_docs()

# ============= EOF =============================================
