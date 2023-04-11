# ===============================================================================
# Copyright 2013 Jake Ross
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
# ===============================================================================

# ============= enthought library imports =======================
import os

from envisage.ui.tasks.task_extension import TaskExtension
from envisage.ui.tasks.task_factory import TaskFactory
from pyface.tasks.action.schema import SMenu
from pyface.tasks.action.schema_addition import SchemaAddition
from traits.api import List, Str

from pychron.core.helpers.filetools import glob_list_directory
from pychron.core.helpers.strtools import to_bool, to_terminator
from pychron.envisage.initialization.initialization_parser import InitializationParser
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.envisage.tasks.list_actions import PatternAction, ShowMotionConfigureAction
from pychron.lasers.laser_managers.ilaser_manager import ILaserManager
from pychron.lasers.tasks.laser_actions import (
    OpenPowerMapAction,
    OpenPatternAction,
    NewPatternAction,
    LaserScriptExecuteAction,
)

# from pychron.lasers.tasks.laser_calibration_task import LaserCalibrationTask
from pychron.paths import paths


def pattern_action(name, application, manager_name, lase=False):
    def factory():
        a = PatternAction(
            id="pattern.action.{}".format(name),
            name=name.capitalize(),
            application=application,
            manager_name=manager_name,
            pattern_path=os.path.join(paths.pattern_dir, name),
            lase=lase,
        )
        return a

    return factory


class CoreClientLaserPlugin(BaseTaskPlugin):
    pass


class CoreLaserPlugin(BaseTaskPlugin):
    def _task_extensions_default(self):
        actions = [
            SchemaAddition(factory=OpenPowerMapAction, path="MenuBar/file.menu/Open"),
            SchemaAddition(
                id="Open Pattern",
                factory=OpenPatternAction,
                path="MenuBar/file.menu/Open",
            ),
            SchemaAddition(
                id="New Pattern", factory=NewPatternAction, path="MenuBar/file.menu/New"
            ),
        ]

        return [TaskExtension(actions=actions)]


class BaseLaserPlugin(BaseTaskPlugin):
    # managers = List(contributes_to="pychron.hardware.managers")
    klass = None
    mode = None

    task_name = None
    accelerator = None

    def _tasks_default(self):
        return [
            TaskFactory(
                id=self.id,
                task_group="hardware",
                factory=self._task_factory,
                name=self.task_name,
                image="laser",
                accelerator=self.accelerator,
            ),
        ]

    def test_communication(self):
        man = self._get_manager()
        return man.test_connection()

    def _service_offers_default(self):
        """ """
        if self.klass is None:
            raise NotImplementedError

        so = self.service_offer_factory(
            protocol=ILaserManager, factory=self._manager_factory
        )
        return [so]

    def _manager_factory(self):
        """ """

        ip = InitializationParser()
        plugin = ip.get_plugin(
            self.klass[1].replace("Manager", ""), category="hardware"
        )
        mode = ip.get_parameter(plugin, "mode")
        self.mode = mode
        klass = ip.get_parameter(plugin, "klass")
        if klass is None and mode == "client":
            klass = "PychronLaserManager"
            pkg = "pychron.lasers.laser_managers.pychron_laser_manager"
            factory = __import__(pkg, fromlist=[klass])
            klassfactory = getattr(factory, klass)
        else:
            factory = __import__(self.klass[0], fromlist=[self.klass[1]])
            klassfactory = getattr(factory, self.klass[1])

        params = dict(name=self.name)
        if mode == "client":
            try:
                tag = ip.get_parameter(plugin, "communications", element=True)
                for attr in [
                    "host",
                    "port",
                    "kind",
                    "timeout",
                    "baudrate",
                    "parity",
                    "stopbits",
                    "message_frame",
                    ("write_terminator", to_terminator),
                    ("use_end", to_bool),
                ]:
                    func = None
                    if isinstance(attr, tuple):
                        attr, func = attr

                    try:
                        elem = tag.find(attr)
                        if elem is not None:
                            v = elem.text.strip()
                            if func:
                                v = func(v)

                            params[attr] = v
                        else:
                            self.debug("No communications attribute {}".format(attr))
                    except Exception as e:
                        print("client comms fail a", attr, e)
            except Exception as e:
                print("client comms fail b", e)

        m = klassfactory(**params)
        m.mode = mode
        m.bootstrap()
        m.plugin_id = self.id
        m.bind_preferences(self.id)
        return m

    def _managers_default(self):
        """ """
        d = []

        if self.klass is not None:
            d = [
                dict(name=self.name, plugin_name=self.name, manager=self._get_manager())
            ]

        return d

    def _get_manager(self):
        return self.application.get_service(
            ILaserManager, 'name=="{}"'.format(self.name)
        )

        # def execute_pattern(self, name):
        #     self._get_manager().execute_pattern(name)
        # def _preferences_default(self):
        #     root = paths.preferences_dir
        #     path = os.path.join(root, 'preferences.ini')
        #     if not os.path.isfile(path):
        #         with open(path, 'w'):
        #             pass
        #     return ['file://{}'.format(path)]

    def _setup_pattern_extensions(self, exts, actions=None):
        if actions is None:
            actions = []

        lactions = []
        for f in glob_list_directory(
            paths.pattern_dir, extension=".lp", remove_extension=True
        ):
            actions.append(
                SchemaAddition(
                    id="pattern.{}".format(f),
                    factory=pattern_action(f, self.application, self.name),
                    path="MenuBar/laser.menu/patterns.menu",
                )
            )
            lactions.append(
                SchemaAddition(
                    id="pattern.lase.{}".format(f),
                    factory=pattern_action(f, self.application, self.name, lase=True),
                    path="MenuBar/laser.menu/patterns.lase.menu",
                )
            )

        if actions:
            actions.insert(
                0,
                SchemaAddition(
                    id="patterns.menu",
                    factory=lambda: SMenu(name="Execute Patterns", id="patterns.menu"),
                    path="MenuBar/laser.menu",
                ),
            )

            lactions.insert(
                0,
                SchemaAddition(
                    id="patterns.lase.menu",
                    factory=lambda: SMenu(
                        name="Execute and Lase Patterns", id="patterns.lase.menu"
                    ),
                    path="MenuBar/laser.menu",
                ),
            )

            exts.append(TaskExtension(actions=lactions))
            exts.append(TaskExtension(actions=actions))
        else:
            self.warning(
                'no patterns scripts located in "{}"'.format(paths.pattern_dir)
            )

    def _create_task_extensions(self):
        exts = []
        if self.mode != "client":

            def efactory():
                return SMenu(id="laser.menu", name="Laser")

            actions = [
                SchemaAddition(
                    id="Laser",
                    factory=efactory,
                    path="MenuBar",
                    before="tools.menu",
                    after="view.menu",
                )
            ]

            exts = [TaskExtension(actions=actions)]

        return exts


class FusionsPlugin(BaseLaserPlugin):
    sources = List(contributes_to="pychron.video.sources")

    def _sources_default(self):
        ip = InitializationParser()
        plugin = ip.get_plugin(self.task_name.replace(" ", ""), category="hardware")
        source = ip.get_parameter(plugin, "video_source")
        rs = []
        if source:
            rs = [(source, self.task_name)]
        return rs

    def _task_extensions_default(self):
        exts = self._create_task_extensions()

        if self.mode != "client":
            actions = [
                SchemaAddition(
                    factory=ShowMotionConfigureAction, path="MenuBar/laser.menu"
                ),
                SchemaAddition(
                    factory=LaserScriptExecuteAction, path="MenuBar/laser.menu"
                ),
            ]
            self._setup_pattern_extensions(exts, actions)

        return exts


# ============= EOF =============================================
