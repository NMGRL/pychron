#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from envisage.ui.tasks.task_factory import TaskFactory
from pyface.tasks.action.schema_addition import SchemaAddition
from envisage.ui.tasks.task_extension import TaskExtension
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from pychron.extraction_line.extraction_line_manager import ExtractionLineManager
from pychron.extraction_line.tasks.extraction_line_task import ExtractionLineTask
from pychron.extraction_line.tasks.extraction_line_actions import LoadCanvasAction, \
    RefreshCanvasAction
from pychron.extraction_line.tasks.extraction_line_preferences import ExtractionLinePreferences, \
    ExtractionLinePreferencesPane


class ExtractionLinePlugin(BaseTaskPlugin):
    id = 'pychron.extraction_line'

    #    manager = Instance(ExtractionLineManager)
    def _my_task_extensions_default(self):
        return [TaskExtension(actions=[SchemaAddition(id='refresh_canvas',
                                                      factory=RefreshCanvasAction,
                                                      path='MenuBar/Tools'
        )]),

                #TaskExtension(id='pychron.extaction_line',
                #              actions=[SchemaAddition(factory=IsolateChamberAction,
                #                                      path='MenuBar/Tools',
                #                                      )]
                #              )
        ]

    def _service_offers_default(self):
        '''
        '''
        so = self.service_offer_factory(
            protocol=ExtractionLineManager,
            factory=self._factory
            #                            factory=ExtractionLineManager
        )

        #        so1 = self.service_offer_factory(
        #                          protocol = GaugeManager,
        #                          #protocol = GM_PROTOCOL,
        #                          factory = self._gm_factory)

        return [so]

    def _factory(self):
        from pychron.initialization_parser import InitializationParser

        ip = InitializationParser()
        try:
            plugin = ip.get_plugin('ExtractionLine', category='hardware')
            mode = ip.get_parameter(plugin, 'mode')
        #            mode = plugin.get('mode')
        except AttributeError:
            # no epxeriment plugin defined
            mode = 'normal'

        elm = ExtractionLineManager(mode=mode)
        elm.bind_preferences()
        return elm

    def _managers_default(self):
        '''
        '''
        return [
            dict(
                name='extraction_line',
                manager=self.application.get_service(ExtractionLineManager)),
        ]

    def _tasks_default(self):
        ts = [TaskFactory(id='pychron.extraction_line',
                          name='Extraction Line',
                          factory=self._task_factory,
                          accelerator='Ctrl+E',
                          task_group='hardware'
        )]
        return ts

    def _task_factory(self):
        elm = self.application.get_service(ExtractionLineManager)
        t = ExtractionLineTask(manager=elm)
        return t

    def _preferences_panes_default(self):
        return [
            ExtractionLinePreferencesPane
        ]

    #    def _my_task_extensions_default(self):
#        return [TaskExtension(actions=[SchemaAddition(id='Load Canvas',
#                                                      factory=LoadCanvasAction,
#                                                      path='MenuBar/ExtractionLine')])]
#============= EOF =============================================
