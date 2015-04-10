# ===============================================================================
# Copyright 2014 Jake Ross
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
# ============= standard library imports ========================
# ============= local library imports  ==========================
import os

from pychron.core.helpers.filetools import to_bool
from pychron.envisage.initialization.initialization_parser import InitializationParser
from pychron.envisage.initialization.nodes import Plugin, PluginTree, GlobalTree, GlobalValue, InitializationModel


DESCRIPTION_MAP = {'Experiment': 'Execute sets of automated runs',
                   'PyScript': "Edit PyScripts; pychron's internal scripting language",
                   'ArArConstants': 'List of Ar/Ar geochronology constants',
                   'Database': 'SQL database interface',
                   'Loading': 'Laser tray loading plugin',
                   'Processing': 'Ar/Ar Processing plugin',
                   'Entry': 'Enter/Edit irradiation data',
                   'Workspace': 'Git-enabled workspace repository',
                   'DVC': "Pychron's custom Data Version Control system",
                   'SystemMonitor': 'Auto plot analyses and system variables',
                   'MediaServer': 'Image server/client',
                   'LabBook': 'Git-enabled labbook repository',
                   'Video': 'Video server/client',
                   'DashboardServer': 'Publish various laboratory values',
                   'DashboardClient': 'Listen to the Dashboard server',
                   'LabspyClient': 'Labspy client. push updates to the labspy database',
                   'Update': 'Update plugin',
                   'Image': 'Use to take snapshots with a connected camera\n'
                            'and save to file or database',
                   'ExtractionLine': 'Control extraction line components',
                   'ArgusSpectrometer': 'Thermo ArgusVI plugin',
                   'FusionsCO2': 'Photon Machines Fusions CO2',
                   'FusionsDiode': 'Photon Machines Fusions Diode',
                   'FusionsUV': "NMGRL's custom Fusions UV",
                   'ExternalPipette': 'Interface with the APIS pipette system',
                   'CanvasDesigner': 'Visual editor for the Extraction Line Schematic',

                   'Email': 'Allows pychron to send emails',

                   'Use IPC': 'use Inter Process Communication e.g. use RemotHardwareServer',
                   'Ignore Initialization Warnings': 'Ignore initialization warnings',
                   'Ignore Initialization Questions': 'Ignore initialization questions',
                   'Ignore Initializaiton Required': 'Ignore hen initialization "required" tag',
                   'Communication Simulation': 'Simulate communication.\nSet Ethernet timeout to 0',
                   'Dashboard Simulation': 'Use a dummy device if none available'}

DEFAULT_PLUGINS = (('General', ('Experiment',
                                'PyScript',
                                'ArArConstants',
                                'Loading',
                                'Processing',
                                'Database',
                                'DVC',
                                'Entry',
                                'SystemMonitor',
                                'DashboardServer',
                                'DashboardClient',
                                'LabspyClient',
                                'Workspace',
                                'LabBook',
                                'MediaServer',
                                'Update',
                                'Video',
                                'Image',
                                'CanvasDesigner')),
                   ('Hardware', ('ArgusSpectrometer',
                                 'ExtractionLine',
                                 'FusionsCO2',
                                 'FusionsDiode',
                                 'FusionsUV',
                                 'ExternalPipette')),
                   ('Social', ('Email',)))

DEFAULT_GLOBALS = (('Use IPC', 'use_ipc'),
                   ('Use Startup Tests', 'use_startup_tests'),
                   ('Ignore Initialization Warnings', 'ignore_initialization_warnings'),
                   ('Ignore Initialization Questions', 'ignore_initialization_questions'),
                   ('Ignore Initialization Required', 'ignore_initialization_required'),
                   ('Communication Simulation', 'communication_simulation'),
                   ('Dashboard Simulation', 'dashboard_simulation'),)

DEFAULTS_MAP = {'Ar Data Reduction': {'globals': ('Use Startup Tests',),
                                      'general': ('Processing', 'Database', 'Entry', 'ArArConstants'),
                                      'hardware': None,
                                      'social': None},
                'Extraction Line': {'globals': ('Use IPC', 'Use Startup Tests',),
                                    'general': None,
                                    'hardware': ('ExtractionLine', ),
                                    'social': ('Email',)},
                'Loading': {'globals': None,
                            'general': ('Database', 'Loading', 'Image', 'Entry'),
                            'hardware': None,
                            'social': None},
                'Experiment': {'globals': ('Use Startup Tests',),
                               'general': ('Experiment', 'Database', 'ArArConstants', 'PyScript', 'Entry',),
                               'hardware': ('ArgusSpectrometer', 'ExtractionLine'),
                               'social': ('Email',)},
                'Experiment CO2': {'globals': ('Use Startup Tests',),
                                   'general': ('Experiment', 'Database', 'ArArConstants', 'PyScript'),
                                   'hardware': ('ArgusSpectrometer', 'ExtractionLine', 'FusionsCO2'),
                                   'social': ('Email',)},
                'Experiment Diode': {'globals': ('Use Startup Tests',),
                                     'general': ('Experiment', 'Database', 'ArArConstants', 'PyScript'),
                                     'hardware': ('ArgusSpectrometer', 'ExtractionLine', 'FusionsDiode'),
                                     'social': ('Email',)},
                'Experiment UV': {'globals': ('Use Startup Tests',),
                                  'general': ('Experiment', 'Database', 'ArArConstants', 'PyScript'),
                                  'hardware': ('ArgusSpectrometer', 'ExtractionLine', 'FusionsUV'),
                                  'social': ('Email',)}}

NOMINAL_DEFAULTS = ['Ar Data Reduction',
                    'Loading',
                    'Experiment',
                    'Experiment CO2',
                    'Experiment Diode',
                    'Experiment UV',
                    'Extraction Line']


def load_plugin_tree():
    p = PluginTree(name='Plugins')
    plugins = []
    for name, ps in DEFAULT_PLUGINS:
        pss = [Plugin(name=pp) for pp in ps]
        plugins.append(PluginTree(name=name, plugins=pss))
    p.plugins = plugins

    return p


def load_global_tree():
    vs = []
    for name, tag in DEFAULT_GLOBALS:
        vs.append(GlobalValue(name=name, tag=tag))

    tree = GlobalTree(values=vs)
    return tree


def get_tree(gi, tree):
    for plugin in tree.plugins:
        if isinstance(plugin, PluginTree):
            if plugin.name.lower() == gi.lower():
                return plugin
            else:
                t = get_tree(gi, plugin)
                if t:
                    return t


def get_plugin(name, tree):
    for plugin in tree.plugins:
        if isinstance(plugin, Plugin):
            if plugin.name.lower() == name.lower():
                return plugin


def get_initialization_model():
    ip = InitializationParser()
    rtree = load_plugin_tree()
    gtree = load_global_tree()
    for gi in ip.get_plugin_groups():
        tree = get_tree(gi, rtree)
        if tree:
            for pp in ip.get_plugins(gi, element=True):
                plugin = get_plugin(pp.text.strip(), tree)
                if plugin:
                    plugin.enabled = to_bool(pp.get('enabled'))

    for gi in ip.get_globals():
        gv = gtree.get_value(gi.tag)
        if gv:
            gv.enabled = to_bool(gi.text.strip())

    model = InitializationModel(trees=[gtree, rtree],
                                path_name=os.path.basename(ip.path),
                                parser=ip)
    model.init_hash()

    return model

# ============= EOF =============================================


