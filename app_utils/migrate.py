# ===============================================================================
# Copyright 2015 Jake Ross
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

# ============= enthought library imports =======================
# ============= standard library imports ========================
import argparse
# ============= local library imports  ==========================
import os
import shutil

VERSION = '1'


def migrate():
    args = get_args()
    root = args.root[0]
    if root is None:
        root = os.path.join(os.path.expanduser('~'), 'Pychron')

    print 'Using root: {}'.format(root)
    version = get_version(root)
    if version == '0':
        migrate_spectrometer_config(root)
        migrate_mftable(root)

    write_version(root)


# migrations
def migrate_mftable(root):
    mfroot = os.path.join(root, 'setupfiles', 'spectrometer', 'mftables')
    spec_root = os.path.join(root, 'setupfiles', 'spectrometer')
    if not os.path.isdir(mfroot):
        os.mkdir(mfroot)

    # move mftable
    mfpath = os.path.join(spec_root, 'mftable.csv')
    if os.path.isfile(mfpath):
        shutil.move(mfpath, os.path.join(mfroot, 'argon.csv'))

    ppath = os.path.join(root, '.hidden', 'mftable_name')
    with open(ppath, 'w') as wfile:
        wfile.write('argon.csv')


def migrate_spectrometer_config(root):
    # make configuration dir
    spec_root = os.path.join(root, 'setupfiles', 'spectrometer')
    config_root = os.path.join(spec_root, 'configurations')
    if not os.path.isdir(config_root):
        os.mkdir(config_root)

    # move config file
    cpath = os.path.join(spec_root, 'config.cfg')
    if os.path.isfile(cpath):
        shutil.move(cpath, os.path.join(config_root, 'argon.cfg'))

    # set persistence
    ppath = os.path.join(root, '.hidden', 'spectrometer_config_name')
    with open(ppath, 'w') as wfile:
        wfile.write('argon.cfg')


def write_version(root):
    p = os.path.join(root, '.hidden', 'version')
    with open(p, 'w') as wfile:
        wfile.write(VERSION)


def get_version(root):
    v = '0'
    p = os.path.join(root, '.hidden', 'version')
    if os.path.isfile(p):
        with open(p, 'r') as rfile:
            v = rfile.read().strip()
    return v


def get_args():
    parser = argparse.ArgumentParser(description='Migrate the Pychron directory')
    parser.add_argument(
        '-r',
        '--root',
        type=str,
        nargs=1,
        help='set the root directory')
    return parser.parse_args()


if __name__ == '__main__':
    migrate()
# ============= EOF =============================================
