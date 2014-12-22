# ===============================================================================
# Copyright 2014 Jake Ross
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
import ast
import os

# ============= standard library imports ========================
# ============= local library imports  ==========================
import shutil
import yaml
from pychron.core.helpers.filetools import unique_dir, list_directory


def migrate_directory(root, clean=False):
    """
        create a migrated directory
    """

    dest = unique_dir(root, 'migrated')
    for p in list_directory(root, extension='.py'):
        migrate_file(p, root, dest, clean)


def comment(ostream, line, tag, clean):
    if line.startswith(tag):
        if not clean:
            li = '#{}'.format(line)
            ostream.write(li)
        return True


def new_method(ostream, line, tag, nmeth, clean):
    if line.startswith(tag):
        if not clean:
            li = '    #{}\n'.format(line.strip())
            ostream.write(li)
        ostream.write('    {}\n'.format(nmeth))
        return True


def migrate_file(p, srcroot, destroot, clean):
    """
        if clean=True dont comment out changes just remove them
    """
    src = os.path.join(srcroot, p)
    dest = os.path.join(destroot, p)

    has_default_fits = False
    #examine docstr
    with open(src, 'r') as fp:
        srctxt = fp.read()
        m = ast.parse(srctxt)
        docstr = ast.get_docstring(m)
        if docstr is not None:
            yd = yaml.load(docstr)
            if yd and 'default_fits' in yd:
                has_default_fits = True
                # print yaml.dump(yd, default_flow_style=False)

    if not has_default_fits:
        doc_updated = False
        with open(src, 'r') as fp, open(dest, 'w') as dfp:
            for li in fp:
                sli = li.strip()
                if not doc_updated:
                    #search for start of docstr

                    if sli == '"""' or sli == "'''":
                        dfp.write(li)
                        dfp.write('{}\n'.format('default_fits: nominal_fits'))
                        doc_updated = True
                else:
                    if comment(dfp, li, 'FITS=', clean):
                        continue
                    if comment(dfp, li, 'BASELINE_FITS=', clean):
                        continue
                    if new_method(dfp, li, '    set_fits', 'set_fits()', clean):
                        continue
                    if new_method(dfp, li, '    set_baseline_fits', 'set_baseline_fits()', clean):
                        continue

                    dfp.write(li)

    else:
        shutil.copyfile(src, dest)


if __name__ == '__main__':
    root = '/Users/ross/Pychrondata_dev/scripts/migration_test'
    migrate_directory(root, clean=True)
# ============= EOF =============================================

