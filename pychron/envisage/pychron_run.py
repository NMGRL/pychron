# ===============================================================================
# Copyright 2011 Jake Ross
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
import logging
from operator import attrgetter

from envisage.core_plugin import CorePlugin
from pyface.message_dialog import warning

from pychron.core.displays.gdisplays import gTraceDisplay
from pychron.envisage.initialization.initialization_parser import InitializationParser
from pychron.envisage.key_bindings import update_key_bindings
from pychron.envisage.tasks.base_plugin import BasePlugin
from pychron.envisage.tasks.tasks_plugin import PychronTasksPlugin, myTasksPlugin
from pychron.logger.tasks.logger_plugin import LoggerPlugin
from pychron.user.tasks.plugin import UsersPlugin
from pychron.pychron_constants import LASER_PLUGINS

logger = logging.getLogger()

PACKAGE_DICT = dict(
    UsagePlugin="pychron.usage.tasks.plugin",
    ArArConstantsPlugin="pychron.constants.tasks.arar_constants_plugin",
    DashboardServerPlugin="pychron.dashboard.tasks.server.plugin",
    DashboardClientPlugin="pychron.dashboard.tasks.client.plugin",
    DatabasePlugin="pychron.database.tasks.database_plugin",
    LabspyClientPlugin="pychron.labspy.tasks.plugin",
    # PsychoDramaPlugin='pychron.psychodrama.tasks.plugin',
    UpdatePlugin="pychron.updater.tasks.update_plugin",
    # data reduction
    MassSpecPlugin="pychron.mass_spec.tasks.plugin",
    DVCPlugin="pychron.dvc.tasks.dvc_plugin",
    GitLabPlugin="pychron.git.tasks.gitlab_plugin",
    GitHubPlugin="pychron.git.tasks.github_plugin",
    LocalGitPlugin="pychron.git.tasks.local_plugin",
    PipelinePlugin="pychron.pipeline.tasks.plugin",
    SparrowPlugin="pychron.sparrow.tasks.plugin",
    GISPlugin="pychron.gis.tasks.plugin",
    ClassifierPlugin="pychron.classifier.tasks.plugin",
    MDDPlugin="pychron.mdd.tasks.plugin",
    AutoPlugin="pychron.pipeline.tasks.auto_plugin",
    MachineLearningPlugin="pychron.ml.tasks.plugin",
    CaffeinePlugin="pychron.caffeine.tasks.plugin",
    # data mappers
    USGSVSCDataPlugin="pychron.data_mapper.tasks.usgs_vsc.plugin",
    WiscArDataPlugin="pychron.data_mapper.tasks.wiscar.plugin",
    # experiment
    EntryPlugin="pychron.entry.tasks.entry_plugin",
    ExperimentPlugin="pychron.experiment.tasks.experiment_plugin",
    PyScriptPlugin="pychron.pyscripts.tasks.pyscript_plugin",
    WatchDogPlugin="pychron.watchdog.tasks.plugin",
    # hardware
    ClientExtractionLinePlugin="pychron.extraction_line.tasks.client_extraction_line_plugin",
    ExternalPipettePlugin="pychron.external_pipette.tasks.external_pipette_plugin",
    ExtractionLinePlugin="pychron.extraction_line.tasks.extraction_line_plugin",
    NMGRLFurnacePlugin="pychron.furnace.tasks.nmgrl.furnace_plugin",
    NMGRLFurnaceControlPlugin="pychron.furnace.tasks.nmgrl.furnace_control_plugin",
    LDEOFurnacePlugin="pychron.furnace.tasks.ldeo.furnace_plugin",
    LDEOFurnaceControlPlugin="pychron.furnace.tasks.ldeo.furnace_control_plugin",
    ThermoFurnacePlugin="pychron.furnace.tasks.thermo.furnace_plugin",
    # hardware-lasers
    TAPDiodePlugin="pychron.lasers.tasks.plugins.tap",
    OsTechDiodePlugin="pychron.lasers.tasks.plugins.ostech_diode",
    AblationCO2Plugin="pychron.lasers.tasks.plugins.ablation_co2",
    ChromiumCO2Plugin="pychron.lasers.tasks.plugins.chromium_co2",
    ChromiumDiodePlugin="pychron.lasers.tasks.plugins.chromium_diode",
    ChromiumUVPlugin="pychron.lasers.tasks.plugins.chromium_uv",
    FusionsDiodePlugin="pychron.lasers.tasks.plugins.diode",
    FusionsCO2Plugin="pychron.lasers.tasks.plugins.co2",
    FusionsUVPlugin="pychron.lasers.tasks.plugins.uv",
    LoadingPlugin="pychron.loading.tasks.loading_plugin",
    CoreLaserPlugin="pychron.lasers.tasks.plugins.laser_plugin",
    CoreClientLaserPlugin="pychron.lasers.tasks.plugins.laser_plugin",
    # spectrometers
    ArgusSpectrometerPlugin="pychron.spectrometer.tasks.thermo.argus",
    HelixSpectrometerPlugin="pychron.spectrometer.tasks.thermo.helix",
    HelixSFTSpectrometerPlugin="pychron.spectrometer.tasks.thermo.helix",
    MapSpectrometerPlugin="pychron.spectrometer.tasks.map_spectrometer_plugin",
    NGXSpectrometerPlugin="pychron.spectrometer.tasks.isotopx.ngx",
    OPCSpectrometerPlugin="pychron.spectrometer.tasks.opc.base",
    # resources
    MediaStoragePlugin="pychron.media_storage.tasks.plugin",
    ImagePlugin="pychron.image.tasks.image_plugin",
    VideoPlugin="pychron.image.tasks.video_plugin",
    # outside database/repositories
    IGSNPlugin="pychron.igsn.tasks.igsn_plugin",
    GeochronPlugin="pychron.geochron.tasks.geochron_plugin",
    # social
    EmailPlugin="pychron.social.email.tasks.plugin",
    GoogleCalendarPlugin="pychron.social.google_calendar.tasks.plugin",
    TwitterPlugin="pychron.social.twitter.plugin",
    # WorkspacePlugin='pychron.workspace.tasks.workspace_plugin',
    # LabBookPlugin='pychron.labbook.tasks.labbook_plugin',
    # SystemMonitorPlugin='pychron.system_monitor.tasks.system_monitor_plugin',
    # CanvasDesignerPlugin='pychron.canvas.tasks.canvas_plugin',
    # MediaServerPlugin='pychron.media_server.tasks.media_server_plugin',
    # ProcessingPlugin='pychron.processing.tasks.processing_plugin',
)


def get_module_name(klass):
    words = []
    wcnt = 0
    for c in klass:
        if c.upper() == c:
            words.append(c.lower())
            wcnt += 1
        else:
            words[wcnt - 1] += c

    return "_".join(words)


def get_hardware_plugins():
    ip = InitializationParser()

    ps = []
    if "hardware" in ip.get_categories():
        from pychron.hardware.tasks.hardware_plugin import HardwarePlugin

        if ip.get_plugins("hardware"):
            ps = [
                HardwarePlugin(),
            ]
    return ps


def get_klass(package, name):
    try:
        m = __import__(package, globals(), locals(), [name])
        klass = getattr(m, name)

    except ImportError as e:
        import traceback

        klass = None
        msg = "****** {} could not be imported {} ******".format(name, e)
        logger.warning(msg, extra={"threadName_": "Launcher"})
        warning(None, msg)
        logger.debug(traceback.format_exc())

    return klass


def get_plugin(pname):
    klass = None
    if not pname.endswith("Plugin"):
        pname = "{}Plugin".format(pname)

    if pname in PACKAGE_DICT:
        package = PACKAGE_DICT[pname]
        klass = get_klass(package, pname)
    else:
        logger.warning(
            "****** {} not a valid plugin name******".format(pname),
            extra={"threadName_": "Launcher"},
        )

    if klass is not None:
        plugin = klass()
        if isinstance(plugin, BasePlugin):
            check = plugin.check()
            if check is True:
                return plugin
            else:
                logger.warning(
                    "****** {} not available {}******".format(klass, check),
                    extra={"threadName_": "Launcher"},
                )
                warning(None, "Failed loading plugin.\n    {}".format(plugin.name))

        else:
            logger.warning(
                "***** Invalid {} needs to be a subclass of Plugin ******".format(
                    klass
                ),
                extra={"threadName_": "Launcher"},
            )


def get_user_plugins():
    """ """

    plugins = []
    ip = InitializationParser()
    ps = ip.get_plugins()

    core_added = False
    for p in ps:
        # if laser plugin add CoreLaserPlugin
        if p in LASER_PLUGINS:
            plugint = ip.get_plugin(p, category="hardware")
            mode = ip.get_parameter(plugint, "mode")
            if mode == "client":
                plugin = get_plugin("CoreClientLaserPlugin")
            else:
                plugin = get_plugin("CoreLaserPlugin")

            if plugin and not core_added:
                core_added = True
                plugins.append(plugin)

        plugin = get_plugin(p)
        if plugin:
            plugins.append(plugin)

    plugins = list(sorted(plugins, key=attrgetter("name")))

    dvcplugin = next((p for p in plugins if p.name == "DVCPlugin"), None)
    if dvcplugin is not None:
        # ensure a githost plugin is available
        githost = next(
            (p for p in plugins if p.name in ("GitHubPlugin", "LocalGitPlugin")), None
        )
        if githost is None:
            plugins.append(get_plugin("LocalGitPlugin"))

        # make githost plugin run prior to dvc plugin
        plugins.remove(githost)
        plugins.insert(0, githost)

    updateplugin = next((p for p in plugins if p.name == "UpdatePlugin"), None)
    if updateplugin is not None:
        plugins.remove(updateplugin)
        plugins.insert(0, updateplugin)
        # p = plugins.pop(idx)
        # plugins.insert(0, p)

    return plugins


def app_factory(klass):
    """
    assemble the plugins
    return a Pychron TaskApplication
    """
    pychron_plugin = PychronTasksPlugin()

    plugins = [
        CorePlugin(),
        myTasksPlugin(),
        pychron_plugin,
        LoggerPlugin(),
        UsersPlugin(),
    ]

    plugins.extend(get_hardware_plugins())
    plugins.extend(get_user_plugins())

    app = klass(plugins=plugins)

    # set key bindings
    update_key_bindings(pychron_plugin.actions)

    return app


def launch(klass):
    """ """
    # login protection
    #
    # moving app.run to a compiled object would be more robust
    #
    # from pychron.login.login import check_login
    # from pychron.paths import paths
    # import os
    # with open(os.path.join(paths.hidden_dir, 'login_pwd'), 'r') as rfile:
    #     if not check_login(fp.read()):
    #         logger.critical('Login failed')
    #         return

    app = app_factory(klass)

    try:
        try:
            import qdarktheme

            qdarktheme.setup_theme("light")
        except ImportError:
            pass

        # root = os.path.dirname(__file__)
        # r = QtGui.QApplication.instance()
        # p = os.path.join(root, 'stylesheets', 'qdark.css')
        # with open(p) as rfile:
        #     r.setStyleSheet(rfile.read())

        app.run()

    except Exception:
        logger.info("Quitting {}".format(app.name), extra={"threadName_": "Launcher"})
        logger.exception("Launching error")
        import traceback

        tb = traceback.format_exc()
        gTraceDisplay.add_text(tb)
        gTraceDisplay.edit_traits(kind="livemodal")

        # finally:
        #     sys.exit(0)


# ============= EOF ====================================
