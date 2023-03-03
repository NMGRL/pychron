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
from types import FunctionType

root = os.path.dirname(os.path.dirname(__file__))
sys.path.append(root)

from pychron.pyscripts.pyscript import PyScript
from pychron.pyscripts.extraction_line_pyscript import ExtractionPyScript


def assemble_docs():
    s = ExtractionPyScript()
    commands = s.get_commands()
    contents = []
    for ci in commands:
        func = getattr(s, ci[1])

        try:
            closure = (c.cell_contents for c in func.__closure__)
            f = next((c for c in closure if isinstance(c, FunctionType)), None)
            docstr = f.__doc__
            # print(f, f.__doc__)
        except TypeError as e:
            docstr = func.__doc__

        if docstr is None:
            docstr = ""

        command = f"### {ci[0]}\n{docstr}\n\n"
        contents.append(command)

    s.set_default_context()

    context = []
    for k, v in s._ctx.items():
        context.append(f"### {k}\n    Type: {type(v).__name__}\n\n")

    context = "\n".join(context)
    print("asfd", context)
    contents = "\n".join(contents)
    content = f"# Pyscript API\n## Commands\n{contents}\n## Context\n{context}"
    pname = os.environ.get("PNAME", "pyscriptdocs.md")
    with open(os.path.join(root, "pychron", pname), "w") as wfile:
        wfile.write(content)


if __name__ == "__main__":
    assemble_docs()

# ============= EOF =============================================
