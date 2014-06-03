# ===============================================================================
# Copyright 2014 Jake Ross
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
import argparse
import os
import subprocess
#============= standard library imports ========================
#============= local library imports  ==========================
def make_root(ver):
    root = os.path.join(os.path.expanduser('~'), 'Pychrondata{}'.format(ver))
    return root


def get_source(root, url=None):
    if url is None:
        url = 'https://github.com/NMGRL/pychron.git'

    repo_name, _ = os.path.splitext(os.path.basename(url))

    wd = os.path.join(root, '.hidden', 'updates')
    # clone src code

    if not os.path.isdir(root):
        os.mkdir(root)
        os.mkdir(os.path.join(root, '.hidden'))
        os.mkdir(wd)

        os.chdir(wd)
        subprocess.call(['git', 'clone', url])
        os.chdir(os.path.join(wd, repo_name))

    else:
        os.chdir(os.path.join(wd, repo_name))
        subprocess.call(['git', 'pull'])


def install_dependencies(env, requirements):
    """
        env: name of a new or existing conda environment
        requirements: path to a requirements file
    """
    if not subprocess.call(["conda", 'create', '--quiet', '--yes', '-n', env, 'python']):
        return

    if not subprocess.call(['source', 'activate', env]):
        return

    if not subprocess.call(["conda", 'install', '--quite', '--yes', '--file', requirements]):
        return

    return True


def build_application(app, version):
    """
        don't call app_maker directly. this way it will build with the correct conda environment
    """
    if not subprocess.call(['python', 'app_utils/app_maker.py', '-A{}'.format(app), '-v{}'.format(version)]):
        return


def parse_args():
    parser = argparse.ArgumentParser(description='Install a pychron application and all its dependencies')
    # parser.add_argument('-A', '--applications',
    #                     nargs=1,
    #                     type=str,
    #                     # default=['pychron', 'remote_hardware_server', 'bakeout'],
    #                     help='set applications to build. valid flavors {}'.format(flavorstr)),
    # parser.add_argument('-v', '--version',
    #                     nargs=1,
    #                     type=str,
    #                     default=['1.0'],
    #                     help='set the version number e.g 1.0')
    #
    # parser.add_argument(
    #     '-r',
    #     '--root',
    #     type=str,
    #     nargs=1,
    #     default='.',
    #     help='set the root directory')

    return parser.parse_args()


def main():
    args = parse_args()

    make_root()


if __name__ == '__main__':
    main()

#============= EOF =============================================
