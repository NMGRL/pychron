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
import os
#============= local library imports  ==========================

version_id = '_uv-2.1.0'
from helpers import build_version

'''
    debug=True inserts the pychron source directory into the PYTHONPATH
    necessary if you are launching from commandline or eclipse(?).
    Use false (default) if your are launching from a standalone bundle.
'''
DEBUG = True
build_version(version_id, debug=DEBUG)


def main():
    '''
        entry point
    '''

    from pychron.envisage.pychron_run import launch
    from pychron.helpers.logger_setup import logging_setup
    from pychron.paths import build_directories, paths

    # import application
    from pychron.applications.pyuv import PyUV as app

    # build directories
    build_directories(paths)

    #    from src.helpers.paths import hidden_dir
    #    path = os.path.join(hidden_dir, 'version_info')
    #    a = VersionInfoDisplay(local_path=path,
    #                           src_path=os.path.join(SRC_DIR,
    #                           'version_info.txt'))
    #    a.check()
    logging_setup('pychron', level='DEBUG')

    #===============================================================================
    # test flag
    # set if you want to execute tests after startup
    # explicitly set the flag here once. mode is a readonly property
    #===============================================================================
    from pychron.globals import globalv

    globalv._test = False
    globalv.debug = DEBUG

    launch(app)
    os._exit(0)


# def profile_code():
#    '''
#    '''
#
#    import cProfile
# #    app_path = '/Users/Ross/Programming/pychron_beta/application_launch.py'
# #    l = open(app_path, 'r')
#    cProfile.run('main()', 'profile.out')
#    import pstats
#    p = pstats.Stats('profile.out')
#    p.strip_dirs()
#    p.sort_stats('time')
#
#    p.print_stats(1000)
#
#    os._exit(0)
# #    sys.exit()
if __name__ == '__main__':
    main()
#============= EOF =============================================

