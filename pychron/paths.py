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
from os import path, mkdir
import os

from pychron.file_defaults import TASK_EXTENSION_DEFAULT, SIMPLE_UI_DEFAULT, EDIT_UI_DEFAULT


class Paths(object):
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
    scripts_dir = scripts_dir = None
    experiment_dir = None
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
    setup_dir = setup_dir = None
    device_dir = None
    spectrometer_dir = None
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
    processed_dir = None
    image_cache_dir = None
    default_cache = None
    loading_dir = None
    power_map_dir = None
    labbook_dir = None
    data_det_ic_dir = None
    sample_image_dir = None
    sample_image_backup_dir = None

    project_dir = None
    meta_dir = None
    meta_db = None
    # vcs_dir = None
    # initialization_dir = None
    # device_creator_dir = None

    # ==============================================================================
    # processing
    # ==============================================================================
    formatting_dir = None

    # ==============================================================================
    # lovera exectuables
    # ==============================================================================
    clovera_root = None

    # ===========================================================================
    # files
    # ===========================================================================
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
    screen_formatting_options = None
    presentation_formatting_options = None
    display_formatting_options = None
    plotter_options = None
    task_extensions_file = None
    simple_ui_file = None
    edit_ui_defaults = None

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
        # ==============================================================================
        # setup
        # ==============================================================================
        self.setup_dir = setup_dir = join(root, 'setupfiles')
        self.spectrometer_dir = join(setup_dir, 'spectrometer')
        self.backup_deflection_dir = join(self.spectrometer_dir, 'deflection_backup')
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

        self.irradiation_tray_maps_dir = join(setup_dir, 'irradiation_tray_maps')
        # ==============================================================================
        # data
        # ==============================================================================
        self.data_dir = data_dir = join(root, 'data')
        self.spectrometer_scans_dir = join(data_dir, 'spectrometer_scans')
        self.modeling_data_dir = join(data_dir, 'modeling')
        self.argus_data_dir = join(data_dir, 'argusVI')
        self.positioning_error_dir = join(data_dir, 'positioning_error')
        self.snapshot_dir = join(data_dir, 'snapshots')
        self.video_dir = join(data_dir, 'videos')
        self.stage_visualizer_dir = join(data_dir, 'stage_visualizer')
        self.data_det_ic_dir = join(data_dir, 'det_ic')
        # self.arar_dir = join(data_dir, 'arar')

        self.isotope_dir = join(self.data_dir, 'isotopes')
        self.workspace_root_dir = join(self.data_dir, 'workspaces')
        self.default_workspace_dir = join(self.workspace_root_dir, 'collection')
        self.processed_dir = join(self.data_dir, 'processed')
        # initialization_dir = join(setup_dir, 'initializations')
        # device_creator_dir = join(device_dir, 'device_creator')
        self.image_cache_dir = join(self.data_dir, 'image_cache')
        self.default_cache = join(self.data_dir, 'cache')
        self.loading_dir = join(self.data_dir, 'loads')
        self.power_map_dir = join(self.data_dir, 'power_maps')
        self.labbook_dir = join(self.data_dir, 'labbook')
        self.sample_image_dir = join(self.data_dir, 'sample_image_dir')
        self.sample_image_backup_dir = join(self.sample_image_dir, 'backup')

        self.project_dir = join(self.data_dir, 'projects')
        self.meta_dir = join(self.data_dir, 'meta')
        self.meta_db = join(self.meta_dir, 'pychronmeta.sqlite')
        # self.vcs_dir = join(self.data_dir, 'vcs')

        # ==============================================================================
        # processing
        # ==============================================================================
        self.formatting_dir = join(self.setup_dir, 'formatting')
        # ==============================================================================
        # lovera exectuables
        # ==============================================================================
        # self.clovera_root = join(pychron_src_root, 'pychron', 'modeling', 'lovera', 'bin')
        # =======================================================================
        # files
        # =======================================================================
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
        self.screen_formatting_options = join(self.formatting_dir, 'screen.yaml')
        self.presentation_formatting_options = join(self.formatting_dir, 'presentation.yaml')
        self.display_formatting_options = join(self.formatting_dir, 'display.yaml')
        self.plotter_options = join(self.plotter_options_dir, 'plotter_options.p')
        self.task_extensions_file = join(self.hidden_dir, 'task_extensions.yaml')
        self.simple_ui_file = join(self.hidden_dir, 'simple_ui.yaml')
        self.edit_ui_defaults = join(self.hidden_dir, 'edit_ui.yaml')

    def write_defaults(self):
        if os.environ.get('TRAVIS_CI', 'False') == 'False' and \
                        os.environ.get('RTD', 'False') == 'False':
            self._write_default_files()

    def _write_default_files(self):
        from pychron.file_defaults import DEFAULT_INITIALIZATION, DEFAULT_STARTUP_TESTS, \
            SYSTEM_HEALTH

        for p, d in ((path.join(self.setup_dir, 'initialization.xml'), DEFAULT_INITIALIZATION),
                     (self.startup_tests, DEFAULT_STARTUP_TESTS),
                     (self.system_health, SYSTEM_HEALTH),
                     (self.simple_ui_file, SIMPLE_UI_DEFAULT),
                     (self.edit_ui_defaults, EDIT_UI_DEFAULT),
                     (self.task_extensions_file, TASK_EXTENSION_DEFAULT)):
            overwrite = d in (SYSTEM_HEALTH, SIMPLE_UI_DEFAULT, TASK_EXTENSION_DEFAULT)
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
paths.build('_dev')
build_directories()
# ============= EOF ==============================================
# ==============================================================================
# # #database
# # ==============================================================================
# device_scan_root = device_scan_root = None
# device_scan_db = None
#
# co2laser_db_root = None
# co2laser_db = None
#
# diodelaser_db_root = None
# diodelaser_db = None
#
# isotope_db_root = None
# isotope_db = None
# ==============================================================================
# #database
# ==============================================================================
# db_path = '/usr/local/pychron
# db_path = stable_root
# self.device_scan_root = device_scan_root = join(db_path, 'device_scans')
# self.device_scan_db = join(device_scan_root, 'device_scans.sqlite')

# self.co2laser_db_root = join(db_path, 'co2laserdb')
# self.co2laser_db = join(db_path, 'co2.sqlite')
# self.uvlaser_db_root = join(db_path, 'uvlaserdb')
# self.uvlaser_db = join(db_path, 'uv.sqlite')
#
# self.powermap_db_root = join(db_path, 'powermap')
# self.powermap_db = join(db_path, 'powermap.sqlite')
#
# self.diodelaser_db_root = join(db_path, 'diodelaserdb')
# self.diodelaser_db = join(db_path, 'diode.sqlite')
# self.isotope_db_root = join(db_path, 'isotopedb')

# ROOT = '/Users/ross/Sandbox/pychron_test_data/data'
# self.isotope_db = join(ROOT, 'isotopedb.sqlite')