# ===============================================================================
# Copyright 2012 Jake Ross
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
from traits.etsconfig.api import ETSConfig

ETSConfig.toolkit = "qt4"

# ============= enthought library imports =======================
# ============= standard library imports ========================
import os
import sys
import logging

# ============= local library imports  ==========================
from pyface.message_dialog import information

logger = logging.getLogger()


def entry_point(modname, klass, setup_version_id='', debug=False):
    """
        entry point
    """

    user = initialize_version(modname, debug)
    set_commandline_args()

    # import app klass and pass to launch function
    mod = __import__('pychron.applications.{}'.format(modname), fromlist=[klass])
    from pychron.envisage.pychron_run import launch

    launch(getattr(mod, klass), user)


def set_commandline_args():
    from pychron.globals import globalv
    import argparse

    parser = argparse.ArgumentParser(description='Generate a password')
    parser.add_argument('-t', '--testbot',
                        action='store')
    args = parser.parse_args()
    globalv.use_testbot = args.testbot


def initialize_version(appname, debug):
    root = os.path.dirname(__file__)

    if not debug:
        add_eggs(root)
    else:
        build_sys_path()

    # can now use pychron.
    from pychron.envisage.user_login import get_user

    user = get_user()
    if not user:
        logger.info('user login failed')
        os._exit(0)

    if appname.startswith('py'):
        appname = appname[2:]

    from pychron.paths import paths

    pref_path = os.path.join(paths.base, '.enthought',
                             'pychron.{}.application.{}'.format(appname, user),
                             'preferences.ini')

    from ConfigParser import ConfigParser

    cp = ConfigParser()
    cp.read(pref_path)

    try:
        proot = cp.get('pychron.general', 'root_dir')
    except BaseException, e:
        print 'root_dir exception={}'.format(e)
        proot = None
        information(None, 'Pychron root directory not set in Preferences/General. Defaulting to "Pychron"')

    if not os.path.isdir(proot):
        information(None, 'Pychron root directory "{}" is not a valid location. Defaulting to "Pychron"'.format(proot))
        proot = None

    if proot is None:
        proot = os.path.join(os.path.expanduser('~'), 'Pychron')

    paths.build(proot)

    # build globals
    build_globals(debug)

    from pychron.core.helpers.logger_setup import logging_setup, set_exception_handler
    from pychron.paths import build_directories

    # build directories
    build_directories()

    # setup logging. set a basename for log files and logging level
    logging_setup('pychron', level='DEBUG')
    if not debug:
        set_exception_handler()

    return user


def build_sys_path():
    """
        need to launch from terminal
    """

    sys.path.insert(0, os.getcwd())


def add_eggs(root):
    egg_path = os.path.join(root, 'pychron.pth')
    if os.path.isfile(egg_path):
        # use a pychron.pth to get additional egg paths
        with open(egg_path, 'r') as fp:
            eggs = [ei.strip() for ei in fp.read().split('\n')]
            eggs = [ei for ei in eggs if ei]

            for egg_name in eggs:
                # sys.path.insert(0, os.path.join(root, egg_name))
                sys.path.append(os.path.join(root, egg_name))


def build_globals(debug):
    try:
        from pychron.envisage.initialization.initialization_parser import InitializationParser
    except ImportError, e:
        from pyface.message_dialog import warning

        warning(None, str(e))

    ip = InitializationParser()

    from pychron.globals import globalv

    globalv.build(ip)
    globalv.debug = debug


# ============= EOF =============================================
