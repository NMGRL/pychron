#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = "qt4"
#============= standard library imports ========================
#============= local library imports  ==========================


from helpers import build_version
build_version()


def main():
    """
        entry point
    """
    from pychron.envisage.pychron_run import launch
    from pychron.core.helpers.logger_setup import logging_setup
    from pychron.paths import build_directories, paths

    # build directories
    build_directories(paths)

#    from pychron.core.helpers.paths import hidden_dir
#    path = os.path.join(hidden_dir, 'version_info')
#    a = VersionInfoDisplay(local_path=path,
#                           src_path=os.path.join(SRC_DIR,
#                           'version_info.txt'))
#    a.check()
    logging_setup('pychron', level='DEBUG')

    from pychron.applications.pyexperiment import PyExperiment as app
    launch(app)

if __name__ == '__main__':

    main()
#============= EOF =============================================
