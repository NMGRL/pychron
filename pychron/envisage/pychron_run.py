# ===============================================================================
# Copyright 2011 Jake Ross
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
import os

from envisage.core_plugin import CorePlugin
from envisage.api import Plugin
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.displays.gdisplays import gTraceDisplay
from pychron.envisage.tasks.tasks_plugin import myTasksPlugin
from pychron.core.helpers.logger_setup import new_logger
from pychron.globals import globalv
from pychron.logger.tasks.logger_plugin import LoggerPlugin
from pychron.initialization_parser import InitializationParser
from pychron.envisage.user_login import user_login

logger = new_logger('launcher')
try:
    from pychron.updater.tasks.update_plugin import UpdatePlugin
except ImportError:
    logger.warning('Git is required to use UpdatePlugin')
    UpdatePlugin = None

PACKAGE_DICT = dict(
    CanvasDesignerPlugin=    'pychron.canvas.tasks.canvas_plugin',
    ArArConstantsPlugin=     'pychron.constants.tasks.arar_constants_plugin',
    DashboardServerPlugin=   'pychron.dashboard.tasks.server.plugin',
    DatabasePlugin=          'pychron.database.tasks.database_plugin',
    EntryPlugin=             'pychron.entry.tasks.entry_plugin',
    ExperimentPlugin=        'pychron.experiment.tasks.experiment_plugin',
    ExternalPipettePlugin=   'pychron.external_pipette.tasks.external_pipette_plugin',
    ExtractionLinePlugin=    'pychron.extraction_line.tasks.extraction_line_plugin',
    GeoPlugin=               'pychron.geo.tasks.geo_plugin',
    VideoPlugin=             'pychron.image.tasks.video_plugin',
    FusionsDiodePlugin=      'pychron.lasers.tasks.plugins.diode',
    FusionsCO2Plugin=        'pychron.lasers.tasks.plugins.co2',
    FusionsUVPlugin=         'pychron.lasers.tasks.plugins.uv',
    LoadingPlugin=           'pychron.loading.loading_plugin',
    CoreLaserPlugin=         'pychron.lasers.tasks.plugins.laser_plugin',
    MediaServerPlugin=       'pychron.media_server.tasks.media_server_plugin',
    ProcessingPlugin=        'pychron.processing.tasks.processing_plugin',
    PyScriptPlugin=          'pychron.pyscripts.tasks.pyscript_plugin',
    ArgusSpectrometerPlugin= 'pychron.spectrometer.tasks.argus_spectrometer_plugin',
    MapSpectrometerPlugin=   'pychron.spectrometer.tasks.map_spectrometer_plugin',
    EmailPlugin=             'pychron.social.tasks.email_plugin',
    SystemMonitorPlugin=     'pychron.system_monitor.tasks.system_monitor_plugin',
    WorkspacePlugin=         'pychron.workspace.tasks.workspace_plugin')


def get_module_name(klass):
    words = []
    wcnt = 0
    for c in klass:
        if c.upper() == c:
            words.append(c.lower())
            wcnt += 1
        else:
            words[wcnt - 1] += c

    return '_'.join(words)


def get_hardware_plugins():
    ip = InitializationParser()

    ps = []
    if 'hardware' in ip.get_categories():
        from pychron.hardware.tasks.hardware_plugin import HardwarePlugin

        if ip.get_plugins('hardware'):
            ps = [HardwarePlugin(), ]
    return ps


def get_klass(package, name):
    try:
        m = __import__(package, globals(), locals(), [name], -1)
        klass = getattr(m, name)

    except ImportError, e:
        import traceback

        traceback.print_exc()
        klass = None
        logger.warning('****** {} could not be imported {} ******'.format(name, e),
                       extra={'threadName_': 'Launcher'})
    return klass


def get_plugin(pname):
    klass = None
    if not pname.endswith('Plugin'):
        pname = '{}Plugin'.format(pname)

    #print PACKAGE_DICT.keys()
    #print pname,pname in PACKAGE_DICT.keys()
    if pname in PACKAGE_DICT:
        package = PACKAGE_DICT[pname]
        klass = get_klass(package, pname)
    elif pname == 'Update':
        klass = UpdatePlugin

    else:
        logger.warning('****** {} not a valid plugin name******'.format(pname),
                       extra={'threadName_': 'Launcher'})

    if klass is not None:
        plugin = klass()
        if isinstance(plugin, Plugin):
            check = plugin.check()
            if check is True:
                return plugin
            else:
                logger.warning('****** {} not available {}******'.format(klass, check),
                               extra={'threadName_': 'Launcher'})
        else:
            logger.warning('***** Invalid {} needs to be a subclass of Plugin ******'.format(klass),
                           extra={'threadName_': 'Launcher'})


def get_user_plugins():
    """
    """
    # append plugins dir to the sys path
    #    sys.path.append(plugins_dir)

    plugins = []
    ps = InitializationParser().get_plugins()

    core_added = False
    for p in ps:
        # if laser plugin add CoreLaserPlugin
        if p in ('FusionsCO2', 'FusionsDiode'):
            plugin = get_plugin('CoreLaserPlugin')
            if plugin and not core_added:
                core_added = True
                plugins.append(plugin)

        plugin = get_plugin(p)
        if plugin:
            plugins.append(plugin)

    return plugins


def app_factory(klass, user):
    """
        assemble the plugins
        return a Pychron TaskApplication
    """
    plugins = [
        CorePlugin(),
        myTasksPlugin(),
        LoggerPlugin()]

    # if UpdatePlugin is not None:
    #     plugins.append(UpdatePlugin())

    plugins += get_hardware_plugins()
    plugins += get_user_plugins()

    app = klass(username=user, plugins=plugins)
    return app


def check_dependencies():
    """
        check the dependencies and
    """
    from pyface.api import warning

    try:
        mod = __import__('uncertainties',
                         fromlist=['ver'])
        ver = mod.__version__
    except ImportError:
        warning(None, 'Install "{}" package. required version>={} '.format('uncertainties', '2.1'))
        return

    vargs = ver.split('.')
    maj = vargs[0]
    if int(maj) < 2:
        warning(None, 'Update "{}" package. your version={}. required version>={} '.format('uncertainties',
                                                                                           ver,
                                                                                           '2.1'))
        return

    return True


def launch(klass):
    """
    """
    # login protection
    #
    # moving app.run to a compiled object would be more robust
    #
    # from pychron.login.login import check_login
    # from pychron.paths import paths
    # import os
    # with open(os.path.join(paths.hidden_dir, 'login_pwd'), 'r') as fp:
    #     if not check_login(fp.read()):
    #         logger.critical('Login failed')
    #         return

    if not check_dependencies():
        logger.info('check dependencies failed')
        os._exit(0)

    user = user_login()
    if not user:
        logger.info('user login failed')
        os._exit(0)

    app = app_factory(klass, user)

    try:
        app.run()
        logger.info('Quitting {}'.format(app.name), extra={'threadName_': 'Launcher'})
    except Exception:
        logger.exception('Launching error')
        import traceback

        tb = traceback.format_exc()
        gTraceDisplay.add_text(tb)
        gTraceDisplay.edit_traits(kind='livemodal')

    finally:
        app.exit()
        os._exit(0)

    return


#============= EOF ====================================
