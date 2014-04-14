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

version_id = ''
from helpers import build_version

'''
    set_path=True inserts the pychron source directory into the PYTHONPATH
    necessary if you are launching from commandline or eclipse(?). 
    Use false (default) if your are launching from a standalone bundle. 
'''
DEBUG = True
build_version(version_id, setup_ver='_view', debug=DEBUG)


def main():
    """
        entry point
    """
    from pychron.envisage.pychron_run import launch
    from pychron.core.helpers.logger_setup import logging_setup
    from pychron.paths import build_directories, paths

    # build directories
    build_directories(paths)

    logging_setup('pychron', level='DEBUG')

    #===============================================================================
    # test flag
    # set if you want to execute tests after startup
    # explicitly set the flag here once. mode is a readonly property
    #===============================================================================
    from pychron.globals import globalv

    globalv._test = False
    globalv.debug = DEBUG

    #import application
    from pychron.applications.pyview import PyView as app

    launch(app)


if __name__ == '__main__':
    main()
#============= EOF =============================================
