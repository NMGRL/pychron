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

# import gc
# print gc.get_threshold()
# gc.set_debug(gc.DEBUG_LEAK| gc.DEBUG_STATS)
#============= standard library imports ========================
#============= local library imports  ==========================

source_version_id = ''
setup_version_id='_dev'
from helpers import build_version
build_version(source_version_id,
              setup_version_id, debug=True)
def setup():
    """
        entry point
    """
    
    from pychron.core.helpers.logger_setup import logging_setup
    from pychron.paths import build_directories, paths

    # import application
#    from pychron.applications.pydiode import PyDiode as app
    from pychron.applications.pyexperiment import PyExperiment as app


    # build directories
    build_directories(paths)

    #

#    from pychron.core.helpers.paths import hidden_dir
#    path = os.path.join(hidden_dir, 'version_info')
#    a = VersionInfoDisplay(local_path=path,
#                           src_path=os.path.join(SRC_DIR,
#                           'version_info.txt'))
#    a.check()
    logging_setup('pychron', level='DEBUG')

# #===============================================================================
# # test flag
# # set if you want to execute tests after startup
# # explicitly set the flag here once. mode is a readonly property
# #===============================================================================
#     from pychron.globals import globalv
#     globalv._test = False
#     globalv.debug = DEBUG
    return app


def main():
    from pychron.envisage.pychron_run import launch
    app=setup()
    launch(app)

if __name__ == '__main__':
    
    main()
#============= EOF =============================================
