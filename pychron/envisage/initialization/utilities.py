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
from __future__ import absolute_import

import os

from pychron.core.helpers.strtools import to_bool
from pychron.envisage.initialization.initialization_parser import InitializationParser
from pychron.envisage.initialization.nodes import (
    Plugin,
    PluginTree,
    GlobalTree,
    GlobalValue,
    InitializationModel,
)

DESCRIPTION_MAP = {
    "Experiment": "Execute sets of automated runs",
    "MassSpec": "Mass Spec plugin",
    "PyScript": "Edit PyScripts; pychron's internal scripting language",
    "ArArConstants": "List of Ar/Ar geochronology constants",
    "Database": "SQL database interface",
    "Loading": "Laser tray loading plugin",
    # 'Processing': 'Ar/Ar Processing plugin',
    "Classifier": "Use Machine learning to classify analyses",
    "Entry": "Enter/Edit irradiation data",
    # 'Workspace': 'Git-enabled workspace repository',
    "DVC": "Pychron's custom Data Version Control system",
    "GitLab": "Private git repository hosting",
    "GitHub": "Public git repository hosting at GitHub.com",
    "LocalGit": "local git repositories",
    "MediaStorage": "Media storage and access",
    "LabBook": "Git-enabled labbook repository",
    "Video": "Video server/client",
    "DashboardServer": "Publish various laboratory values",
    "DashboardClient": "Listen to the Dashboard server",
    "LabspyClient": "Labspy client. push updates to the labspy database",
    "Update": "Update plugin",
    "Image": "Use to take snapshots with a connected camera\n"
    "and save to file or database",
    "ExtractionLine": "Control extraction line components",
    "ClientExtractionLine": "Remotely control extraction line components",
    "ArgusSpectrometer": "Thermo ArgusVI plugin",
    "HelixSpectrometer": "Thermo Helix plugin",
    "HelixSFTSpectrometer": "Thermo Helix SFT plugin",
    "NGXSpectrometer": "Isotopx NGX plugin",
    "NMGRLFurnace": "NMGRL's resistance furnace plugin",
    "ThermoFurnace": "Thermo's resistance furnace plugin",
    "FusionsCO2": "Photon Machines Fusions CO2",
    "FusionsDiode": "Photon Machines Fusions Diode",
    "FusionsUV": "NMGRL's custom Fusions UV",
    "ExternalPipette": "Interface with the APIS pipette system",
    "CanvasDesigner": "Visual editor for the Extraction Line Schematic",
    "IGSN": "International Geo Sample Number",
    "Email": "Allows pychron to send emails",
    "Pipeline": "Pychron's pipeline based processing workflow",
    "Use IPC": "use Inter Process Communication e.g. use RemotHardwareServer",
    "Ignore Initialization Warnings": "Ignore initialization warnings",
    "Ignore Initialization Questions": "Ignore initialization questions",
    "Ignore Initializaiton Required": 'Ignore hen initialization "required" tag',
    "Communication Simulation": "Simulate communication.\nSet Ethernet timeout to 0",
    "Dashboard Simulation": "Use a dummy device if none available",
}

DEFAULT_PLUGINS = (
    (
        "General",
        (
            "Experiment",
            "MassSpec",
            "PyScript",
            "ArArConstants",
            "Loading",
            "Geochron",
            "IGSN",
            # 'Processing',
            "Database",
            ("DVC", ["test_database", "test_dvc_fetch_meta"]),
            ("GitLab", ["test_api"]),
            ("GitHub", ["test_api"]),
            "LocalGit",
            "Pipeline",
            "Entry",
            "Classifier",
            "DashboardServer",
            "DashboardClient",
            "LabspyClient",
            # 'Workspace',
            "GIS",
            "LabBook",
            "MediaStorage",
            "MDD",
            "Auto",
            "Update",
            ("WatchDog", ["test_api"]),
            "Usage",
        ),
    ),
    ("Data", ("USGSVSCData", "WiscArData", ("Sparrow", ["test_api"]))),
    (
        "Hardware",
        (
            ("ArgusSpectrometer", ["test_communication", "test_intensity"]),
            ("HelixSpectrometer", ["test_communication"]),
            ("HelixSFTSpectrometer", ["test_communication"]),
            ("NGXSpectrometer", ["test_communication"]),
            (
                "ExtractionLine",
                ["test_valve_communication", "test_gauge_communication"],
            ),
            "ClientExtractionLine",
            "NMGRLFurnace",
            "NMGRLFurnaceControl",
            "ThermoFurnace",
            ("AblationCO2", ["test_communication"]),
            ("ChromiumCO2", ["test_communication"]),
            ("ChromiumDiode", ["test_communication"]),
            ("ChromiumUV", ["test_communication"]),
            ("FusionsCO2", ["test_communication"]),
            ("FusionsDiode", ["test_communication"]),
            ("FusionsUV", ["test_communication"]),
            "ExternalPipette",
        ),
    ),
    ("Social", ("Email", "GoogleCalendar")),
)

DEFAULT_GLOBALS = (
    ("Use IPC", "use_ipc"),
    # ('Pipeline Debug', 'pipeline_debug'),
    ("Use Startup Tests", "use_startup_tests"),
    ("Ignore Initialization Warnings", "ignore_initialization_warnings"),
    ("Ignore Initialization Questions", "ignore_initialization_questions"),
    ("Ignore Initialization Required", "ignore_initialization_required"),
    ("Ignore Connection Warnings", "ignore_connection_warnings"),
    ("Communication Simulation", "communication_simulation"),
    ("Dashboard Simulation", "dashboard_simulation"),
)

DEFAULTS_MAP = {
    "Ar Data Reduction": {
        "globals": ("Use Startup Tests",),
        "general": ("Pipeline", "DVC", "Entry", "ArArConstants"),
        "hardware": None,
        "social": None,
    },
    "Extraction Line": {
        "globals": (
            "Use IPC",
            "Use Startup Tests",
        ),
        "general": None,
        "hardware": ("ExtractionLine",),
        "social": ("Email",),
    },
    "Loading": {
        "globals": None,
        "general": ("DVC", "Loading", "Image", "Entry"),
        "hardware": None,
        "social": None,
    },
    "Experiment": {
        "globals": ("Use Startup Tests",),
        "general": (
            "Experiment",
            "DVC",
            "ArArConstants",
            "PyScript",
            "Entry",
        ),
        "hardware": ("ArgusSpectrometer", "ClientExtractionLine"),
        "social": ("Email",),
    },
    "Experiment CO2": {
        "globals": ("Use Startup Tests",),
        "general": ("Experiment", "DVC", "ArArConstants", "PyScript"),
        "hardware": ("ArgusSpectrometer", "ClientExtractionLine", "FusionsCO2"),
        "social": ("Email",),
    },
    "Experiment Diode": {
        "globals": ("Use Startup Tests",),
        "general": ("Experiment", "DVC", "ArArConstants", "PyScript"),
        "hardware": ("ArgusSpectrometer", "ClientExtractionLine", "FusionsDiode"),
        "social": ("Email",),
    },
    "Experiment UV": {
        "globals": ("Use Startup Tests",),
        "general": ("Experiment", "DVC", "ArArConstants", "PyScript"),
        "hardware": ("ArgusSpectrometer", "ClientExtractionLine", "FusionsUV"),
        "social": ("Email",),
    },
}

NOMINAL_DEFAULTS = [
    "Ar Data Reduction",
    "Loading",
    "Experiment",
    "Experiment CO2",
    "Experiment Diode",
    "Experiment UV",
    "Extraction Line",
]


def load_plugin_tree():
    p = PluginTree(name="Plugins")
    plugins = []
    for name, ps in DEFAULT_PLUGINS:
        pss = [Plugin(factory=pp) for pp in ps]
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
            ps = ip.get_plugins(gi, element=True)
            if ps:
                for pp in ps:
                    plugin = get_plugin(pp.text.strip(), tree)
                    if plugin:
                        plugin.enabled = to_bool(pp.get("enabled"))

    for gi in ip.get_globals():
        gv = gtree.get_value(gi.tag)
        if gv:
            gv.enabled = to_bool(gi.text.strip())

    model = InitializationModel(
        trees=[gtree, rtree], path_name=os.path.basename(ip.path), parser=ip
    )
    model.init_hash()

    return model


# ============= EOF =============================================
