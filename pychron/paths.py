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

"""
Global path structure

add a path verification function
make sure directory exists and build if not
"""
# ============= standard library imports ========================
from __future__ import absolute_import
from __future__ import print_function

import os
import pickle
import shutil
from hashlib import md5
from os import path, mkdir, environ

from pychron.file_defaults import (
    TASK_EXTENSION_DEFAULT,
    SIMPLE_UI_DEFAULT,
    EDIT_UI_DEFAULT,
    IDENTIFIERS_DEFAULT,
)


def get_file_text(d):
    txt = ""
    try:
        mod = __import__("pychron.file_defaults", fromlist=[d])
        txt = getattr(mod, d)
    except BaseException as e:
        pass
    return txt


global_hidden = os.path.join(
    path.expanduser("~"), ".pychron.{}".format(os.environ.get("APPLICATION_ID", 0))
)
if not os.path.isdir(global_hidden):
    mkdir(global_hidden)

build_repo = os.path.join(global_hidden, "updates")
users_file = os.path.join(global_hidden, "users")
environments_file = os.path.join(global_hidden, "environments")

resources = os.path.join(path.dirname(path.dirname(__file__)), "resources")

icons = os.path.join(resources, "icons")
dbicons = os.path.join(icons, "database")
arrows = os.path.join(icons, "arrows")
document = os.path.join(icons, "document")
table = os.path.join(icons, "table")
balls = os.path.join(icons, "balls")
octicons = os.path.join(icons, "octicons")

images = os.path.join(resources, "images")
splashes = os.path.join(resources, "splashes")
labspy_templates = os.path.join(resources, "labspy_templates")
abouts = os.path.join(resources, "abouts")
sounds = os.path.join(resources, "sounds")

image_search_path = [images]
icon_search_path = [icons, dbicons, arrows, document, table, balls, octicons]
splash_search_path = [splashes]
about_search_path = [abouts]
sounds_search_path = [sounds]


class Paths(object):
    root = None
    bundle_root = None
    home = path.expanduser("~")

    icons = ""
    images = ""
    splashes = None
    abouts = None
    sounds = None
    app_resources = None

    # _dir suffix ensures the path is checked for existence
    root_dir = root
    stable_root = None
    labspy_templates = None
    labspy_template_search_path = None
    icon_search_path = None
    image_search_path = None
    sound_search_path = None
    splash_search_path = None
    about_search_path = None
    resources = None
    peak_center_config_dir = None
    # ==============================================================================
    # root
    # ==============================================================================
    scripts_dir = None
    experiment_dir = None
    experiment_rem_dir = None
    auto_save_experiment_dir = None

    run_block_dir = None
    generic_experiment_dir = None
    backup_experiment_dir = None
    backup_device_dir = None
    plugins_dir = None
    hidden_dir = None
    appdata_dir = None
    labspy_dir = None
    labspy_context_dir = None

    # login
    login_file = None
    last_login_file = None

    preferences_dir = None
    comment_templates_dir = None
    plotter_options_dir = None
    table_options_dir = None
    test_dir = None
    custom_queries_dir = None
    log_dir = None
    peak_center_config_dir = None
    # ===========================================================================
    # scripts
    # ===========================================================================
    procedures_dir = None
    measurement_dir = None
    post_measurement_dir = None
    extraction_dir = None
    post_equilibration_dir = None
    conditionals_dir = None
    hops_dir = None
    fits_dir = None
    spectrometer_scripts_dir = None
    pipeline_script_dir = None
    # ==============================================================================
    # setup
    # ==============================================================================
    setup_dir = None
    device_dir = None
    spectrometer_dir = None
    spectrometer_config_dir = None
    mftable_dir = None
    backup_deflection_dir = None

    queue_conditionals_dir = None
    canvas2D_dir = None
    canvas3D_dir = None
    extraction_line_dir = None
    monitors_dir = None
    jog_dir = None
    pattern_dir = None
    incremental_heat_template_dir = None

    block_dir = None
    map_dir = None
    furnace_map_dir = None
    user_points_dir = None
    irradiation_tray_maps_dir = None

    # ==============================================================================
    # data
    # ==============================================================================
    data_dir = None
    csv_data_dir = None
    report_dir = None
    mdd_data_dir = None
    argus_data_dir = None
    positioning_error_dir = None
    snapshot_dir = None
    video_dir = None
    stage_visualizer_dir = None
    # default_workspace_dir = None
    # workspace_root_dir = None
    spectrometer_scans_dir = None
    furnace_scans_dir = None
    processed_dir = None
    image_cache_dir = None
    default_cache = None
    loading_dir = None
    load_results_dir = None
    power_map_dir = None
    labbook_dir = None
    data_det_ic_dir = None
    sample_image_dir = None
    sample_image_backup_dir = None
    corrections_dir = None
    figure_dir = None
    table_dir = None

    media_storage_dir = None

    repository_dataset_dir = None
    project_dir = None
    meta_root = None
    dvc_dir = None
    device_scan_dir = None
    isotope_dir = None

    index_db = None
    sample_dir = None

    offline_db_dir = None
    # vcs_dir = None
    # initialization_dir = None
    # device_creator_dir = None

    # ==============================================================================
    # processing
    # ==============================================================================
    user_pipeline_dir = None
    user_pipeline_template_dir = None

    flux_constants = None

    # ==============================================================================
    # lovera exectuables
    # ==============================================================================
    clovera_root = None

    # ===========================================================================
    # files
    # ===========================================================================
    checkpoint_file = None
    labspy_client_config = None
    template_manifest_file = None
    pipeline_template_file = None
    identifiers_file = None
    identifier_mapping_file = None
    backup_recovery_file = None
    last_experiment = None
    mftable = None
    deflection = None
    startup_tests = None
    ic_mftable = None
    mftable_backup_dir = None
    system_conditionals = None
    experiment_defaults = None

    ideogram_defaults = None
    spectrum_defaults = None
    inverse_isochron_defaults = None
    composites_defaults = None
    sys_mon_ideogram_defaults = None
    # screen_formatting_options = None
    # presentation_formatting_options = None
    # display_formatting_options = None
    plotter_options = None
    task_extensions_file = None
    simple_ui_file = None
    edit_ui_defaults = None

    duration_tracker = None
    duration_tracker_frequencies = None
    experiment_launch_history = None
    notification_triggers = None
    furnace_firmware = None

    af_demagnetization = None
    ratio_change_detection = None
    actuation_tracker_file = None

    oauth_file = None
    packages_file = None
    baseline_model = None
    # plot_factory_defaults = (('ideogram_defaults', 'IDEOGRAM_DEFAULTS', True),
    #                          ('spectrum_defaults', 'SPECTRUM_DEFAULTS', True))

    # ('inverse_isochron_defaults', 'INVERSE_ISOCHRON_DEFAULTS', False),
    # ('composites_defaults', 'COMPOSITE_DEFAULTS', False))
    # ('screen_formatting_options', 'SCREEN_FORMATTING_DEFAULTS', False),
    # ('presentation_formatting_options', 'PRESENTATION_FORMATTING_DEFAULTS', False),
    # ('display_formatting_options', 'DISPLAY_FORMATTING_DEFAULTS', False))

    # icfactor_template = None
    # blanks_template = None
    # iso_evo_template = None
    # ideogram_template = None
    # flux_template = None
    # vertical_flux_template = None
    # xy_scatter_template = None
    # csv_ideogram_template = None
    # spectrum_template = None
    # isochron_template = None
    # inverse_isochron_template = None
    # analysis_table_template = None
    # interpreted_age_table_template = None
    # interpreted_age_ideogram_template = None
    # auto_ideogram_template = None
    # auto_series_template = None
    # auto_report_template = None
    # report_template = None
    # series_template = None
    # geochron_template = None
    # yield_template = None
    # csv_analyses_export_template = None
    # radial_template = None
    # regression_series_template = None
    # correction_factors_template = None
    # analysis_metadata_template = None

    furnace_sample_states = None
    valid_pi_names = None

    def write_default_file(self, p, default, overwrite=False):
        return self._write_default_file(p, default, overwrite)

    def build(self, root):
        join = path.join

        # self.version = version
        if root.startswith("_"):
            root = join(self.home, "Pychron{}".format(root))

        if root.startswith("~"):
            root = join(self.home, root[2:])

        if not path.isdir(root):
            mkdir(root)

        sd = join(root, "setupfiles")
        if not path.isdir(sd):
            mkdir(sd)

        root = os.path.normpath(root)
        self.root_dir = root
        self.log_dir = join(root, "logs")

        # ==============================================================================
        # root
        # ==============================================================================
        self.scripts_dir = scripts_dir = join(root, "scripts")
        self.procedures_dir = join(scripts_dir, "procedures")
        self.measurement_dir = join(scripts_dir, "measurement")
        self.post_measurement_dir = join(scripts_dir, "post_measurement")
        self.extraction_dir = join(scripts_dir, "extraction")
        self.post_equilibration_dir = join(scripts_dir, "post_equilibration")
        self.conditionals_dir = join(scripts_dir, "conditionals")
        self.pipeline_script_dir = join(scripts_dir, "pipeline")

        self.hops_dir = join(self.measurement_dir, "hops")
        self.fits_dir = join(self.measurement_dir, "fits")
        self.spectrometer_scripts_dir = join(scripts_dir, "spectrometer")
        self.experiment_dir = join(root, "experiments")
        self.experiment_rem_dir = join(self.experiment_dir, "rem")
        self.auto_save_experiment_dir = join(self.experiment_dir, "auto_save")
        self.run_block_dir = join(self.experiment_dir, "blocks")
        self.generic_experiment_dir = join(self.experiment_dir, "generic")
        self.backup_experiment_dir = join(self.experiment_dir, "backup")

        # self.hidden_dir = join(root, '.hidden')
        self.preferences_dir = join(root, "preferences")
        self.queue_conditionals_dir = join(root, "queue_conditionals")
        # ==============================================================================
        # hidden
        # ==============================================================================
        self.appdata_dir = join(root, ".appdata")
        self.hidden_dir = self.appdata_dir

        self.labspy_dir = join(self.appdata_dir, "labspy")
        self.labspy_context_dir = join(self.labspy_dir, "context")

        self.table_options_dir = join(self.appdata_dir, "table_options")
        self.plotter_options_dir = join(self.appdata_dir, "plotter_options")
        self.comment_templates_dir = join(self.appdata_dir, "comment_templates")

        self.peak_center_config_dir = join(self.appdata_dir, "peak_center_configs")

        self.actuation_tracker_file = join(self.appdata_dir, "actuation_tracker.json")
        self.actuation_tracker_file_yaml = join(
            self.appdata_dir, "actuation_tracker.yaml"
        )

        # login
        self.login_file = join(self.appdata_dir, "login")
        self.last_login_file = join(self.appdata_dir, "last_login")
        # ==============================================================================
        # setup
        # ==============================================================================
        self.setup_dir = setup_dir = join(root, "setupfiles")
        self.spectrometer_dir = join(setup_dir, "spectrometer")
        self.backup_deflection_dir = join(self.spectrometer_dir, "deflection_backup")
        self.spectrometer_config_dir = join(self.spectrometer_dir, "configurations")
        self.mftable_dir = join(self.spectrometer_dir, "mftables")

        self.device_dir = join(setup_dir, "devices")
        self.backup_device_dir = join(self.device_dir, "backup")
        self.canvas2D_dir = join(setup_dir, "canvas2D")
        # self.canvas3D_dir = join(setup_dir, 'canvas3D')
        self.extraction_line_dir = join(setup_dir, "extractionline")
        self.monitors_dir = join(setup_dir, "monitors")
        self.pattern_dir = join(setup_dir, "patterns")
        self.incremental_heat_template_dir = join(
            setup_dir, "incremental_heat_templates"
        )

        self.block_dir = join(setup_dir, "blocks")
        self.map_dir = map_dir = join(setup_dir, "tray_maps")
        self.user_points_dir = join(map_dir, "user_points")
        self.furnace_map_dir = join(map_dir, "furnace")
        # self.irradiation_tray_maps_dir = join(setup_dir, 'irradiation_tray_maps')
        # ==============================================================================
        # data
        # ==============================================================================
        self.data_dir = data_dir = join(root, "data")
        self.csv_data_dir = join(data_dir, "csv")
        self.report_dir = join(data_dir, "reports")
        self.spectrometer_scans_dir = join(data_dir, "spectrometer_scans")
        self.furnace_scans_dir = join(data_dir, "furnace_scans")
        self.mdd_data_dir = join(data_dir, "mdd")
        self.argus_data_dir = join(data_dir, "argusVI")
        self.positioning_error_dir = join(data_dir, "positioning_error")
        self.snapshot_dir = join(data_dir, "snapshots")
        self.video_dir = join(data_dir, "videos")
        self.stage_visualizer_dir = join(data_dir, "stage_visualizer")
        self.data_det_ic_dir = join(data_dir, "det_ic")
        # self.arar_dir = join(data_dir, 'arar')
        self.device_scan_dir = join(data_dir, "device_scans")
        self.isotope_dir = join(self.data_dir, "isotopes")
        # self.workspace_root_dir = join(self.data_dir, 'workspaces')
        # self.default_workspace_dir = join(self.workspace_root_dir, 'collection')
        # self.processed_dir = join(self.data_dir, 'processed')

        self.image_cache_dir = join(self.data_dir, "image_cache")
        self.default_cache = join(self.data_dir, "cache")
        self.loading_dir = join(self.data_dir, "loads")
        self.load_results_dir = join(self.loading_dir, "results")
        self.power_map_dir = join(self.data_dir, "power_maps")
        self.labbook_dir = join(self.data_dir, "labbook")
        self.sample_image_dir = join(self.data_dir, "sample_image_dir")
        self.sample_image_backup_dir = join(self.sample_image_dir, "backup")
        self.figure_dir = join(self.data_dir, "figures")
        self.table_dir = join(self.data_dir, "tables")

        self.corrections_dir = join(self.data_dir, "stage_corrections")
        self.dvc_dir = join(self.data_dir, ".dvc")
        self.repository_dataset_dir = join(self.dvc_dir, "repositories")
        self.meta_root = join(self.dvc_dir, "MetaData")
        self.sample_dir = join(self.data_dir, "sample_entry")
        self.media_storage_dir = join(self.data_dir, "media")
        self.offline_db_dir = join(self.data_dir, "offline_db")
        # ==============================================================================
        # processing
        # ==============================================================================
        # self.formatting_dir = join(self.setup_dir, 'formatting')
        self.user_pipeline_dir = join(self.setup_dir, "pipeline")
        self.user_pipeline_template_dir = join(self.user_pipeline_dir, "templates")

        self.flux_constants = join(self.setup_dir, "flux_constants.yaml")
        # ==============================================================================
        # lovera exectuables
        # ==============================================================================
        self.clovera_root = join(root, "lovera", "bin")
        # =======================================================================
        # files
        # =======================================================================
        # labspy_client_config = join(self.setup_dir, 'labspy_client.yaml')
        # self.template_manifest_file = join(self.pipeline_dir, 'pipeline_manifest.p')
        # self.pipeline_template_file = join(self.pipeline_dir, 'template_order.yaml')
        self.identifiers_file = join(self.appdata_dir, "identifiers.yaml")
        self.identifier_mapping_file = join(self.setup_dir, "identifier_mapping.yaml")
        self.backup_recovery_file = join(self.appdata_dir, "backup_recovery")
        self.last_experiment = join(self.appdata_dir, "last_experiment")
        self.mftable = join(self.spectrometer_dir, "mftables", "mftable.csv")
        self.ic_mftable = join(self.spectrometer_dir, "mftables", "ic_mftable.csv")
        self.mftable_backup_dir = join(self.spectrometer_dir, "mftables", "backup")

        self.deflection = join(self.spectrometer_dir, "deflection.yaml")
        self.startup_tests = join(self.setup_dir, "startup_tests.yaml")
        # self.set_search_paths()
        self.system_conditionals = join(
            self.spectrometer_dir, "system_conditionals.yaml"
        )
        self.experiment_defaults = join(setup_dir, "experiment_defaults.yaml")
        self.ideogram_defaults = join(self.appdata_dir, "ideogram_defaults.yaml")
        self.spectrum_defaults = join(self.appdata_dir, "spectrum_defaults.yaml")
        self.inverse_isochron_defaults = join(
            self.appdata_dir, "inverse_isochron_defaults.yaml"
        )
        self.composites_defaults = join(self.appdata_dir, "composite_defaults.yaml")

        self.plotter_options = join(self.plotter_options_dir, "plotter_options.p")
        self.task_extensions_file = join(self.appdata_dir, "task_extensions.yaml")
        self.simple_ui_file = join(self.appdata_dir, "simple_ui.yaml")
        self.edit_ui_defaults = join(self.appdata_dir, "edit_ui.yaml")

        self.duration_tracker = join(self.appdata_dir, "duration_tracker.txt")
        self.duration_tracker_frequencies = join(
            self.appdata_dir, "duration_tracker_frequencies.txt"
        )
        self.experiment_launch_history = join(
            self.appdata_dir, "experiment_launch_history.txt"
        )
        self.notification_triggers = join(self.setup_dir, "notification_triggers.yaml")

        self.furnace_firmware = join(self.setup_dir, "furnace_firmware.yaml")
        self.furnace_sample_states = join(
            self.appdata_dir, "furnace_sample_states.yaml"
        )
        self.valid_pi_names = join(self.setup_dir, "valid_pi_names.yaml")

        self.af_demagnetization = join(
            paths.spectrometer_dir, "af_demagnetization.yaml"
        )

        self.ratio_change_detection = join(
            paths.setup_dir, "ratio_change_detection.yaml"
        )

        self.oauth_file = join(self.appdata_dir, "oauth.json")

        self.packages_file = join(self.appdata_dir, "packages.json")

        self.baseline_model = join(
            self.scripts_dir, "syn_extraction", "baseline_model.csv"
        )

        build_directories()

        migrate_hidden()
        migrate_pyview()

    def set_template_manifest(self, files):
        # open the manifest file to set the overwrite flag
        manifest = self._get_manifest()
        for item in files:
            fn, t, o = item
            txt = get_file_text(t)
            h = md5(txt).hexdigest()
            if fn in manifest and h == manifest[fn]:
                item[2] = False

            manifest[fn] = h

        with open(paths.template_manifest_file, "w") as wfile:
            pickle.dump(manifest, wfile)

        return files

    def update_manifest(self, name, text):
        manifest = self._get_manifest()
        manifest[name] = md5(text).hexdigest()

    def _get_manifest(self):
        if path.isfile(paths.template_manifest_file):
            with open(paths.template_manifest_file) as rfile:
                manifest = pickle.load(rfile)
        else:
            manifest = {}
        return manifest

    def hidden_path(self, basename):
        # from pychron.globals import globalv
        # basename = '{}.{}'.format(basename, globalv.username)
        return path.join(self.appdata_dir, basename)

    def write_defaults(self):
        if (
            environ.get("TRAVIS_CI", "False") == "False"
            and environ.get("RTD", "False") == "False"
        ):
            self._write_default_files()

    def reset_plot_factory_defaults(self):
        from pyface.message_dialog import warning

        warning(None, "Reset plot factor defaults not enabled")
        # self.write_file_defaults(self.plot_factory_defaults, force=True)

    def write_file_defaults(self, fs, force=False):
        for args in fs:
            if len(args) == 3:
                p, d, o = args
            else:
                d, o = args
                p = None

            txt = get_file_text(d)
            if p is not None:
                try:
                    p = getattr(paths, p)
                except AttributeError as e:
                    print("write_file_defaults", e)

            self._write_default_file(p, txt, o or force)

    def _write_default_files(self):
        from pychron.file_defaults import DEFAULT_INITIALIZATION, DEFAULT_STARTUP_TESTS

        for p, d in (
            (path.join(self.setup_dir, "initialization.xml"), DEFAULT_INITIALIZATION),
            (self.startup_tests, DEFAULT_STARTUP_TESTS),
            (self.simple_ui_file, SIMPLE_UI_DEFAULT),
            (self.edit_ui_defaults, EDIT_UI_DEFAULT),
            (self.task_extensions_file, TASK_EXTENSION_DEFAULT),
            (self.identifiers_file, IDENTIFIERS_DEFAULT),
        ):
            overwrite = d in (SIMPLE_UI_DEFAULT,)
            self._write_default_file(p, d, overwrite)

    def _write_default_file(self, p, default, overwrite=False):
        if not path.isfile(p) or overwrite:
            with open(p, "w") as wfile:
                wfile.write(default)
                return True

    def _build_templates(self, root):
        for attr in dir(self):
            if attr.endswith("_template") and getattr(self, attr) is None:
                v = path.join(root, "{}.yaml".format(attr[:-9]))
                setattr(self, attr, v)


def r_mkdir(p):
    if p and not path.isdir(p):
        try:
            mkdir(p)
        except OSError:
            r_mkdir(path.dirname(p))
            mkdir(p)


def build_directories():
    # global paths
    # verify paths
    # import copy
    for di in dir(paths):
        if di.endswith("_dir"):
            r_mkdir(getattr(paths, di))


def migrate_pyview():
    pv = os.path.join(paths.appdata_dir, "pyview")
    migrate(pv, os.path.join(paths.appdata_dir, "pycrunch"))


def migrate_hidden():
    hd = os.path.join(paths.root_dir, ".hidden")
    migrate(hd, paths.appdata_dir)


def migrate(src, dest):
    for root, dirs, files in os.walk(src):
        if root == src:
            droot = dest
        else:
            droot = os.path.join(dest, os.path.basename(root))

        if not os.path.isdir(droot):
            os.makedirs(droot)

        for f in files:
            if f not in (".DS_Store",):
                src = os.path.join(root, f)
                dst = os.path.join(droot, f)
                if not os.path.isfile(dst):
                    print("moving {} to {}".format(src, dst))
                    shutil.move(src, dst)


paths = Paths()
# ============= EOF ==============================================
