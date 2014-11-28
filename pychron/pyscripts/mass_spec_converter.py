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

#============= enthought library imports =======================
import os
import shlex
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.paths import paths

KEYWORDS = dict(
              Message='info',
              Gosub='gosub',
              Delay='sleep',
              Open='open',
              Close='close',
              BeginInterval='begin_interval',
              CompleteInterval='complete_interval',
              IF='if',
              END='end'

              )

nindent = 1
INDENT = '    '
def as_pyscript_cmd(l, f):
    global nindent

    l = l.strip()
    if l.startswith("'"):
        r = '#{}'.format(l)
        py_cmd = _build_py_cmd_line(r, nindent)
    else:
        try:
            args = shlex.split(l)
        except:
            l = l.split("'")[0]
            args = shlex.split(l)

        nk = None
        if args:
            k = args[0]
            try:
                nk = KEYWORDS[k]
                args = args[1:]
                nargs = []
                for a in args:
                    try:
                        a = float(a)
                        fmt = '{}'
                    except ValueError:
                        fmt = '"{}"'

                    if nk == 'if':
                        fmt = '{}'
                    nargs.append(fmt.format(a))

                sargs = ','.join(nargs)
                if nk == 'if':
                    r = '{} {}:'.format(nk, sargs)
                else:
                    r = '{}({})'.format(nk, sargs)
            except KeyError:
                r = '#{}'.format(l)
        else:
            r = ''
        if nk == 'end':
            r = '#end\n'
            nindent = 1

        py_cmd = _build_py_cmd_line(r, nindent)

        if nk == 'if':
            nindent = 2


    return py_cmd
#    return nk, r

def _build_py_cmd_line(r, nindent):
    py_cmd = '{}{}\n'.format(INDENT * nindent, r)
    return py_cmd

def to_pyscript(base, root, out, name):
#    print root, out
    n = root[len(base) + 1:]
    if n:
        out = os.path.join(out, n)

    if not os.path.isdir(out):
        os.mkdir(out)

    ip = os.path.join(root, name)
#    name = name.replace(' ', '_')
    op = os.path.join(out, '{}.py'.format(name))

    with open(ip, 'r') as in_f:
        with open(op, 'w') as out_f:

            out_f.write('''
def main():
''')

            for _, l in enumerate(in_f.read().split('\r')):
                cmd = as_pyscript_cmd(l, in_f)
#                if k == 'end':
#                    nindent = 1
#                    cmd = '#end\n'

#                py_cmd = '{}{}\n'.format(INDENT * nindent, cmd)
                out_f.write(cmd)
#                if k == 'if':
#                    nindent = 2


if __name__ == '__main__':
    rt = '/Users/ross/Sandbox/runscripts'
    out = '/Users/ross/Sandbox/runscripts/out'
    out = os.path.join(paths.scripts_dir, 'ms_runscripts')
    name = 'Quick Air x1'

    for root, dirs, files in os.walk(rt):
#        print root, files
        for f in files:
            if f.startswith('.'):
                continue
            if f.endswith('.py'):
                continue
#            print os.path.join(root, f)
            to_pyscript(rt, root, out, f)




# ============= EOF =============================================
