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

#set GUI toolkit to QT
from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = "qt4"
#============= standard library imports ========================
#============= local library imports  ==========================

# from helpers import build_version
# build_version()
source_version_id = ''
setup_version_id='_dev'
from helpers import build_version
build_version(source_version_id,
              setup_version_id, debug=False)

def main():
    """
        entry point
    """

    from pychron.core.helpers.logger_setup import logging_setup
    from pychron.paths import build_directories, paths

    # build directories
    build_directories(paths)

    # setup logging. set a basename for log files and logging level
    logging_setup('pychron', level='DEBUG')

    #import app klass and pass to launch function
    from pychron.applications.pyexperiment import PyExperiment as app
    from pychron.envisage.pychron_run import launch
    launch(app)

if __name__ == '__main__':
    main()
#============= EOF =============================================
