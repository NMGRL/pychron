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


def make_context_item(k, v):
    txt = f"### {k}\n    Type: {type(v).__name__}\n\n"
    return txt


from lazydocs import MarkdownGenerator
generator = MarkdownGenerator()

def assemble_docs():
    s = ExtractionPyScript()
    commands = s.get_commands()
    contents = []
    for ci in sorted(commands, key=lambda x: x[0]):
        func = getattr(s, ci[1])

        try:
            closure = (c.cell_contents for c in func.__closure__)
            func = next((c for c in closure if isinstance(c, FunctionType)), None)

            # docstr = f.__doc__
            # print(f, f.__doc__)
        except TypeError as e:
            # docstr = func.__doc__
            pass

        # if docstr is None:
        #     docstr = ""
        # else:
        docstr = ''
        if func is not None:
            # Select a module (e.g. my_module) to generate markdown documentation
            docstr = generator.func2md(func)

            # command = f"### {ci[0]}\n{docstr}\n\n"
            contents.append(docstr)

    s.set_default_context()

    context = []

    ks = sorted(s._ctx.keys())
    for k in ks:
        if k in ('ex', 'testing_syntax'):
            continue

        v = s._ctx[k]
        txt = make_context_item(k, v)
        context.append(txt)
        # context.append(f"### {k}\n    Type: {type(v).__name__}\n\n")

    context = "\n".join(context)
    contents = "\n".join(contents)
    commandhelptxt = '''
Below are all the available functions that may be used within a PyScript. Python builtins are also available 
and additional modules may be imported similar to any normal python script.
    '''
    contexthelpstr = '''
Below are all the "contextual" values availiable to a PyScript. These contextual values are typically set by the 
Experiment Editor and used when running an Automated Analysis
    '''
    content = f"# Pyscript API\n## Commands\n{commandhelptxt}\n{contents}\n## Context\n{contexthelpstr}\n{context}"
    pname = os.environ.get("PNAME", "pyscriptdocs.md")
    with open(os.path.join(root, "pychron", pname), "w") as wfile:
        wfile.write(content)


if __name__ == "__main__":
    assemble_docs()

# ============= EOF =============================================
