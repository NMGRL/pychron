#===============================================================================
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

from envisage.core_plugin import CorePlugin
from envisage.api import Plugin
#============= standard library imports ========================
#============= local library imports  ==========================
from pyface.message_dialog import warning
from pychron.displays.gdisplays import gTraceDisplay
from pychron.envisage.tasks.tasks_plugin import myTasksPlugin
from pychron.core.helpers.logger_setup import new_logger
from pychron.logger.tasks.logger_plugin import LoggerPlugin
from pychron.initialization_parser import InitializationParser

logger = new_logger('launcher')
try:
    from pychron.updater.tasks.update_plugin import UpdatePlugin
except ImportError:
    logger.warning('Git is required to use UpdatePlugin')
    UpdatePlugin=None




PACKAGE_DICT = dict(
    ExperimentPlugin='pychron.experiment.tasks.experiment_plugin',
    LoadingPlugin='pychron.loading.loading_plugin',
    ExtractionLinePlugin='pychron.extraction_line.tasks.extraction_line_plugin',
    VideoPlugin='pychron.image.tasks.video_plugin',
    #                   CanvasDesignerPlugin='pychron.canvas.plugins.canvas_designer_plugin',
    #                   MDDModelerPlugin='pychron.modeling.plugins.mdd_modeler_plugin',

    #                   SVNPlugin='pychron.svn.plugins.svn_plugin',

    FusionsDiodePlugin='pychron.lasers.tasks.plugins.diode',
    FusionsCO2Plugin='pychron.lasers.tasks.plugins.co2',
    FusionsUVPlugin='pychron.lasers.tasks.plugins.uv',
    CoreLaserPlugin='pychron.lasers.tasks.plugins.laser_plugin',
    #                   FusionsDiodePlugin='pychron.lasers.plugins.fusions.diode.plugin',
    #                   FusionsCO2Plugin='pychron.lasers.plugins.fusions.co2.plugin',
    #                   FusionsUVPlugin='pychron.lasers.plugins.fusions.uv.plugin',

    #                   SynradCO2Plugin='pychron.lasers.plugins.synrad_co2_plugin',

    SpectrometerPlugin='pychron.spectrometer.tasks.spectrometer_plugin',

    #                   GraphPlugin='pychron.graph.plugins.graph_plugin',

    #                   TwitterPlugin='pychron.social.plugins.twitter_plugin',

    EmailPlugin='pychron.social.tasks.email_plugin',
    ProcessingPlugin='pychron.processing.tasks.processing_plugin',

    MediaServerPlugin='pychron.media_server.tasks.media_server_plugin',
    PyScriptPlugin='pychron.pyscripts.tasks.pyscript_plugin',
    DatabasePlugin='pychron.database.tasks.database_plugin',
    CanvasDesignerPlugin='pychron.canvas.tasks.canvas_plugin',
    ArArConstantsPlugin='pychron.constants.tasks.arar_constants_plugin',
    EntryPlugin='pychron.entry.tasks.entry_plugin',
    SystemMonitorPlugin='pychron.system_monitor.tasks.system_monitor_plugin',
    DashboardServerPlugin='pychron.dashboard.tasks.server.plugin',
    GeoPlugin='pychron.geo.tasks.geo_plugin')


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
                       extra={'threadName_': 'Launcher'}
        )
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


def app_factory(klass):
    """
        assemble the plugins
        return a Pychron TaskApplication
    """
    plugins = [
        CorePlugin(),
        myTasksPlugin(),
        LoggerPlugin(),
        ]

    if UpdatePlugin is not None:
        plugins.append(UpdatePlugin())

    plugins += get_hardware_plugins()
    plugins += get_user_plugins()

    app = klass(plugins=plugins)
    return app


def check_dependencies():
    """
        check the dependencies and
    """
    from pyface.api import warning

    try:
        mod = __import__('uncertainties',
                         fromlist=['__version__']
        )
        __version__ = mod.__version__
    except ImportError:
        warning(None, 'Install "{}" package. required version>={} '.format('uncertainties', '2.1'))
        return

    vargs = __version__.split('.')
    maj = vargs[0]
    if int(maj) < 2:
        warning(None, 'Update "{}" package. your version={}. required version>={} '.format('uncertainties',
                                                                                           __version__,
                                                                                           '2.1'
        ))
        return

    return True


def launch(klass):
    """
    """

    if not check_dependencies():
        return

    app = app_factory(klass)

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

    return


#============= EOF ====================================
