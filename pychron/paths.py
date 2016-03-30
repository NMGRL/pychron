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
import os
from os import path, mkdir

from pychron.file_defaults import TASK_EXTENSION_DEFAULT, SIMPLE_UI_DEFAULT, \
    EDIT_UI_DEFAULT, IDENTIFIERS_DEFAULT


def get_file_text(d):
    txt = ''
    try:
        mod = __import__('pychron.file_defaults', fromlist=[d])
        txt = getattr(mod, d)
    except BaseException, e:
        pass
    return txt


class Paths(object):
    git_base_origin = 'https://github.com'

    dissertation = '/Users/ross/Programming/git/dissertation'
    # enthought = path.join(path.expanduser('~'), '.enthought')
    # users_file = path.join(enthought, 'users')
    base = path.expanduser('~')

    # version = None
    root = None
    bundle_root = None
    # pychron_src_root = None
    # doc_html_root = None
    icons = ''
    images = ''
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
    labspy_dir = None
    labspy_context_dir = None
    # users_file = None
    build_repo = None
    login_file = None
    preferences_dir = None
    comment_templates_dir = None
    plotter_options_dir = None
    test_dir = None
    custom_queries_dir = None
    template_dir = None
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
    heating_schedule_dir = None
    map_dir = None
    furnace_map_dir = None
    user_points_dir = None
    irradiation_tray_maps_dir = None
    # ==============================================================================
    # data
    # ==============================================================================
    data_dir = None
    modeling_data_dir = None
    argus_data_dir = None
    positioning_error_dir = None
    snapshot_dir = None
    video_dir = None
    stage_visualizer_dir = None
    default_workspace_dir = None
    workspace_root_dir = None
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

    repository_dataset_dir = None
    project_dir = None
    meta_root = None
    dvc_dir = None
    device_scan_dir = None
    isotope_dir = None

    index_db = None
    # vcs_dir = None
    # initialization_dir = None
    # device_creator_dir = None

    # ==============================================================================
    # processing
    # ==============================================================================
    formatting_dir = None

    pipeline_dir = None
    pipeline_template_dir = None

    user_pipeline_dir = None
    user_pipeline_template_dir = None
    # ==============================================================================
    # lovera exectuables
    # ==============================================================================
    clovera_root = None

    # ===========================================================================
    # files
    # ===========================================================================
    template_manifest_file = None
    pipeline_template_file = None
    identifiers_file = None
    backup_recovery_file = None
    last_experiment = None
    mftable = None
    deflection = None
    startup_tests = None
    ic_mftable = None
    system_conditionals = None
    experiment_defaults = None
    system_health = None

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

    # plot_factory_defaults = (('ideogram_defaults', 'IDEOGRAM_DEFAULTS', True),
    #                          ('spectrum_defaults', 'SPECTRUM_DEFAULTS', True))

    # ('inverse_isochron_defaults', 'INVERSE_ISOCHRON_DEFAULTS', False),
    # ('composites_defaults', 'COMPOSITE_DEFAULTS', False))
    # ('screen_formatting_options', 'SCREEN_FORMATTING_DEFAULTS', False),
    # ('presentation_formatting_options', 'PRESENTATION_FORMATTING_DEFAULTS', False),
    # ('display_formatting_options', 'DISPLAY_FORMATTING_DEFAULTS', False))
    icfactor_template = None
    blanks_template = None
    iso_evo_template = None
    ideogram_template = None
    vertical_flux_template = None
    csv_ideogram_template = None
    spectrum_template = None
    isochron_template = None
    inverse_isochron_template = None
    analysis_table_template = None
    interpreted_age_table_template = None
    auto_ideogram_template = None
    series_template = None

    def write_default_file(self, p, default, overwrite=False):
        return self._write_default_file(p, default, overwrite)

    def set_search_paths(self, app_rec=None):
        self.app_resources = app_rec
        self.set_icon_search_path()
        self.set_splash_search_path()
        self.set_about_search_path()
        self.set_image_search_path()
        self.set_sound_search_path()
        self.set_labspy_template_search_path()

    def set_image_search_path(self):
        self.image_search_path = [self.images,
                                  self.app_resources]

    def set_icon_search_path(self):
        ps = [self.icons, self.app_resources]
        if self.app_resources:
            ps.append(os.path.join(self.app_resources, 'icons'))

        self.icon_search_path = ps

    def set_splash_search_path(self):
        self.splash_search_path = [self.splashes, self.app_resources]

    def set_about_search_path(self):
        self.about_search_path = [self.abouts, self.app_resources]

    def set_sound_search_path(self):
        self.sound_search_path = [self.sounds,
                                  self.app_resources]

    def set_labspy_template_search_path(self):
        self.labspy_template_search_path = [self.labspy_templates,
                                            self.app_resources]

    def build(self, root):
        join = path.join
        # self.version = version
        if root.startswith('_'):
            root = join(path.expanduser('~'), 'Pychron{}'.format(root))

        if not path.isdir(root):
            mkdir(root)

        sd = join(root, 'setupfiles')
        if not path.isdir(sd):
            mkdir(sd)

        self.root_dir = root
        self.log_dir = join(root, 'logs')

        self.resources = join(path.dirname(path.dirname(__file__)), 'resources')
        self.icons = join(self.resources, 'icons')
        self.images = join(self.resources, 'images')
        self.splashes = join(self.resources, 'splashes')
        self.labspy_templates = join(self.resources, 'labspy_templates')
        self.abouts = join(self.resources, 'abouts')
        self.sounds = join(self.resources, 'sounds')

        # ==============================================================================
        # root
        # ==============================================================================
        self.scripts_dir = scripts_dir = join(root, 'scripts')
        self.procedures_dir = join(scripts_dir, 'procedures')
        self.measurement_dir = join(scripts_dir, 'measurement')
        self.post_measurement_dir = join(scripts_dir, 'post_measurement')
        self.extraction_dir = join(scripts_dir, 'extraction')
        self.post_equilibration_dir = join(scripts_dir, 'post_equilibration')
        self.conditionals_dir = join(scripts_dir, 'conditionals')
        self.hops_dir = join(self.measurement_dir, 'hops')
        self.fits_dir = join(self.measurement_dir, 'fits')

        self.experiment_dir = join(root, 'experiments')
        self.experiment_rem_dir = join(self.experiment_dir, 'rem')
        self.auto_save_experiment_dir = join(self.experiment_dir, 'auto_save')
        self.run_block_dir = join(self.experiment_dir, 'blocks')
        self.generic_experiment_dir = join(self.experiment_dir, 'generic')
        self.backup_experiment_dir = join(self.experiment_dir, 'backup')

        self.hidden_dir = join(root, '.hidden')

        self.preferences_dir = join(root, 'preferences')
        self.template_dir = join(root, 'templates')
        self.queue_conditionals_dir = join(root, 'queue_conditionals')
        # ==============================================================================
        # hidden
        # ==============================================================================
        self.labspy_dir = join(self.hidden_dir, 'labspy')
        self.labspy_context_dir = join(self.labspy_dir, 'context')

        self.plotter_options_dir = join(self.hidden_dir, 'plotter_options')
        self.comment_templates_dir = join(self.hidden_dir, 'comment_templates')
        self.build_repo = join(self.hidden_dir, 'updates', 'pychron')
        self.peak_center_config_dir = join(self.hidden_dir, 'peak_center_config_dir')
        # ==============================================================================
        # setup
        # ==============================================================================
        self.setup_dir = setup_dir = join(root, 'setupfiles')
        self.spectrometer_dir = join(setup_dir, 'spectrometer')
        self.backup_deflection_dir = join(self.spectrometer_dir, 'deflection_backup')
        self.spectrometer_config_dir = join(self.spectrometer_dir, 'configurations')
        self.mftable_dir = join(self.spectrometer_dir, 'mftables')

        self.device_dir = join(setup_dir, 'devices')
        self.backup_device_dir = join(self.device_dir, 'backup')
        self.canvas2D_dir = join(setup_dir, 'canvas2D')
        # self.canvas3D_dir = join(setup_dir, 'canvas3D')
        self.extraction_line_dir = join(setup_dir, 'extractionline')
        self.monitors_dir = join(setup_dir, 'monitors')
        self.pattern_dir = join(setup_dir, 'patterns')
        self.incremental_heat_template_dir = join(setup_dir, 'incremental_heat_templates')

        self.block_dir = join(setup_dir, 'blocks')
        self.map_dir = map_dir = join(setup_dir, 'tray_maps')
        self.user_points_dir = join(map_dir, 'user_points')
        self.furnace_map_dir = join(map_dir, 'furnace')
        self.irradiation_tray_maps_dir = join(setup_dir, 'irradiation_tray_maps')
        # ==============================================================================
        # data
        # ==============================================================================
        self.data_dir = data_dir = join(root, 'data')
        self.spectrometer_scans_dir = join(data_dir, 'spectrometer_scans')
        self.furnace_scans_dir = join(data_dir, 'furnace_scans')
        self.modeling_data_dir = join(data_dir, 'modeling')
        self.argus_data_dir = join(data_dir, 'argusVI')
        self.positioning_error_dir = join(data_dir, 'positioning_error')
        self.snapshot_dir = join(data_dir, 'snapshots')
        self.video_dir = join(data_dir, 'videos')
        self.stage_visualizer_dir = join(data_dir, 'stage_visualizer')
        self.data_det_ic_dir = join(data_dir, 'det_ic')
        # self.arar_dir = join(data_dir, 'arar')
        self.device_scan_dir = join(data_dir, 'device_scans')
        self.isotope_dir = join(self.data_dir, 'isotopes')
        # self.workspace_root_dir = join(self.data_dir, 'workspaces')
        # self.default_workspace_dir = join(self.workspace_root_dir, 'collection')
        # self.processed_dir = join(self.data_dir, 'processed')

        self.image_cache_dir = join(self.data_dir, 'image_cache')
        self.default_cache = join(self.data_dir, 'cache')
        self.loading_dir = join(self.data_dir, 'loads')
        self.load_results_dir = join(self.loading_dir, 'results')
        self.power_map_dir = join(self.data_dir, 'power_maps')
        self.labbook_dir = join(self.data_dir, 'labbook')
        self.sample_image_dir = join(self.data_dir, 'sample_image_dir')
        self.sample_image_backup_dir = join(self.sample_image_dir, 'backup')
        self.figure_dir = join(self.data_dir, 'figures')
        self.table_dir = join(self.data_dir, 'tables')

        self.corrections_dir = join(self.data_dir, 'stage_corrections')
        self.dvc_dir = join(self.data_dir, '.dvc')
        self.repository_dataset_dir = join(self.dvc_dir, 'repositories')
        self.meta_root = join(self.dvc_dir, 'MetaData')

        # ==============================================================================
        # processing
        # ==============================================================================
        # self.formatting_dir = join(self.setup_dir, 'formatting')
        self.user_pipeline_dir = join(self.setup_dir, 'pipeline')
        self.user_pipeline_template_dir = join(self.user_pipeline_dir, 'templates')

        self.pipeline_dir = join(self.hidden_dir, 'pipeline')
        self.pipeline_template_dir = join(self.pipeline_dir, 'templates')
        # ==============================================================================
        # lovera exectuables
        # ==============================================================================
        # self.clovera_root = join(pychron_src_root, 'pychron', 'modeling', 'lovera', 'bin')
        # =======================================================================
        # files
        # =======================================================================
        self.template_manifest_file = join(self.pipeline_dir, 'pipeline_manifest.p')
        self.pipeline_template_file = join(self.pipeline_dir, 'template_order.yaml')
        self.identifiers_file = join(self.hidden_dir, 'identifiers.yaml')
        self.backup_recovery_file = join(self.hidden_dir, 'backup_recovery')
        self.last_experiment = join(self.hidden_dir, 'last_experiment')
        self.mftable = join(self.spectrometer_dir, 'mftable.csv')
        self.ic_mftable = join(self.spectrometer_dir, 'ic_mftable.csv')

        self.deflection = join(self.spectrometer_dir, 'deflection.yaml')
        self.startup_tests = join(self.setup_dir, 'startup_tests.yaml')
        self.set_search_paths()
        self.system_conditionals = join(self.spectrometer_dir, 'system_conditionals.yaml')
        self.experiment_defaults = join(setup_dir, 'experiment_defaults.yaml')
        self.ideogram_defaults = join(self.hidden_dir, 'ideogram_defaults.yaml')
        self.spectrum_defaults = join(self.hidden_dir, 'spectrum_defaults.yaml')
        self.inverse_isochron_defaults = join(self.hidden_dir, 'inverse_isochron_defaults.yaml')
        self.composites_defaults = join(self.hidden_dir, 'composite_defaults.yaml')
        self.system_health = join(self.setup_dir, 'system_health.yaml')
        # self.screen_formatting_options = join(self.formatting_dir, 'screen.yaml')
        # self.presentation_formatting_options = join(self.formatting_dir, 'presentation.yaml')
        # self.display_formatting_options = join(self.formatting_dir, 'display.yaml')
        self.plotter_options = join(self.plotter_options_dir, 'plotter_options.p')
        self.task_extensions_file = join(self.hidden_dir, 'task_extensions.yaml')
        self.simple_ui_file = join(self.hidden_dir, 'simple_ui.yaml')
        self.edit_ui_defaults = join(self.hidden_dir, 'edit_ui.yaml')

        self.duration_tracker = join(self.hidden_dir, 'duration_tracker.txt')
        self.duration_tracker_frequencies = join(self.hidden_dir, 'duration_tracker_frequencies.txt')
        self.experiment_launch_history = join(self.hidden_dir, 'experiment_launch_history.txt')
        self.notification_triggers = join(self.setup_dir, 'notification_triggers.yaml')

        self.furnace_firmware = join(self.setup_dir, 'furnace_firmware.yaml')

        # =======================================================================
        # pipeline templates
        # =======================================================================
        self.icfactor_template = join(self.pipeline_template_dir, 'icfactor.yaml')
        self.blanks_template = join(self.pipeline_template_dir, 'blanks.yaml')
        self.iso_evo_template = join(self.pipeline_template_dir, 'iso_evo.yaml')
        self.ideogram_template = join(self.pipeline_template_dir, 'ideogram.yaml')
        self.csv_ideogram_template = join(self.pipeline_template_dir, 'csv_ideogram.yaml')
        self.spectrum_template = join(self.pipeline_template_dir, 'spectrum.yaml')
        self.isochron_template = join(self.pipeline_template_dir, 'isochron.yaml')
        self.inverse_isochron_template = join(self.pipeline_template_dir, 'inverse_isochron.yaml')
        self.vertical_flux_template = join(self.pipeline_template_dir, 'vertical_flux.yaml')
        self.analysis_table_template = join(self.pipeline_template_dir, 'analysis_table.yaml')
        self.interpreted_age_table_template = join(self.pipeline_template_dir, 'interpreted_age_table.yaml')
        self.auto_ideogram_template = join(self.pipeline_template_dir, 'auto_ideogram.yaml')
        self.series_template = join(self.pipeline_template_dir, 'series.yaml')
        build_directories()

    def write_defaults(self):
        if os.environ.get('TRAVIS_CI', 'False') == 'False' and os.environ.get('RTD', 'False') == 'False':
            self._write_default_files()

    def reset_plot_factory_defaults(self):
        from pyface.message_dialog import warning
        warning(None, 'Reset plot factor defaults not enabled')
        # self.write_file_defaults(self.plot_factory_defaults, force=True)

    def write_file_defaults(self, fs, force=False):
        for p, d, o in fs:
            txt = get_file_text(d)
            try:
                p = getattr(paths, p)
            except AttributeError:
                pass
            self.write_default_file(p, txt, o or force)

    def _write_default_files(self):
        from pychron.file_defaults import DEFAULT_INITIALIZATION, DEFAULT_STARTUP_TESTS, SYSTEM_HEALTH

        for p, d in ((path.join(self.setup_dir, 'initialization.xml'), DEFAULT_INITIALIZATION),
                     (self.startup_tests, DEFAULT_STARTUP_TESTS),
                     (self.system_health, SYSTEM_HEALTH),
                     (self.simple_ui_file, SIMPLE_UI_DEFAULT),
                     (self.edit_ui_defaults, EDIT_UI_DEFAULT),
                     (self.task_extensions_file, TASK_EXTENSION_DEFAULT),
                     (self.identifiers_file, IDENTIFIERS_DEFAULT),
                     # (self.pipeline_template_file, PIPELINE_TEMPLATES)
                     ):
            overwrite = d in (SYSTEM_HEALTH, SIMPLE_UI_DEFAULT,)
            # overwrite = d in (SYSTEM_HEALTH, SIMPLE_UI_DEFAULT,)
            # print p
            self._write_default_file(p, d, overwrite)

    def _write_default_file(self, p, default, overwrite=False):
        if not path.isfile(p) or overwrite:
            with open(p, 'w') as wfile:
                wfile.write(default)
                return True


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
    for l in dir(paths):
        if l.endswith('_dir'):
            r_mkdir(getattr(paths, l))


paths = Paths()
# ============= EOF ==============================================
