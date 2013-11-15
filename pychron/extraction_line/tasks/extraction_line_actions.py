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
from pyface.action.api import Action

#============= standard library imports ========================

#============= local library imports  ==========================
# from pychron.envisage.core.action_helper import open_manager

#sample change actions
from pyface.image_resource import ImageResource
from pyface.tasks.action.task_action import TaskAction
from pychron.paths import paths


def icon(name):
    return ImageResource(name='{}.png'.format(name),
                         search_path=paths.icon_search_path)


class IsolateChamberAction(TaskAction):
    name = 'Isolate Chamber'
    method = 'isolate_chamber'
    image = icon('arrow_in')


class EvacuateChamberAction(TaskAction):
    name = 'Evacuate Chamber'
    method = 'evacuate_chamber'
    image = icon('arrow_out')


class FinishChamberChangeAction(TaskAction):
    name = 'Finish'
    method = 'finish_chamber_change'
    image = icon('tick')


class ExtractionLineAction(Action):
    def _get_manager(self, event, app=None):
        EL_PROTOCOL = 'pychron.extraction_line.extraction_line_manager.ExtractionLineManager'
        if app is None:
            app = event.task.window.application
        return app.get_service(EL_PROTOCOL)


class OpenExtractionLineManager(ExtractionLineAction):
    description = 'Open extraction line manager'
    name = 'Open Extraction Line Manager'
    accelerator = 'Ctrl+E'

    def perform(self, event):
        man = self._get_manager(event)

        app = self.window.application
        app.open_view(man)

    #        open_manager(app, man)

class OpenExtractionLineExplanation(ExtractionLineAction):
    description = 'Open extraction line explanation'

    def perform(self, event):
        man = self._get_manager(event)
        app = self.window.application
        app.open_view(man.explanation)

    #        open_manager(app, man.explanation)

class LoadCanvasAction(ExtractionLineAction):
    '''
    '''
    description = 'load an updated canvas file'
    name = 'Load Canvas'
    enabled = False

    def perform(self, event):
        '''
        
        '''
        manager = self._get_manager(event)
        #        manager.window = self.window
        manager.load_canvas()


class RefreshCanvasAction(ExtractionLineAction):
    description = 'reload the scene graph to reflect changes made to setupfiles'
    name = 'Refresh Canvas'
    #    enabled = False
    def perform(self, event):
        manager = self._get_manager(event)
        #        manager.window = self.window
        manager.reload_canvas()


# class OpenViewControllerAction(ExtractionLineAction):
#    description = 'Open User views'
#    name = 'Open User Views'
#    enabled = True
#
# #    def __init__(self, *args, **kw):
# #        super(OpenViewControllerAction, self).__init__(*args, **kw)
# #
# #        man = get_manager(self.window)
# #        man.on_trait_change(self.update, 'ui')
# #
# #    def update(self, obj, name, old, new):
# #        if new:
# #            self.enabled = True
# #        else:
# #            self.enabled = False
#
#    def perform(self, event):
#        '''
#        '''
#        manager = self._get_manager(event)
#        app = self.window.application
#        app.open_view(manager.view_controller)
# #        open_manager(app, manager.view_controller, kind='livemodal',
# #                     parent=manager.ui.control
# #                     )


# class OpenDeviceStreamerAction(Action):
#    description = 'Open the device streamer manager'
#    name = 'Open Device Streamer'
#
#    enabled = False
#
#    def __init__(self, *args, **kw):
#        super(OpenDeviceStreamerAction, self).__init__(*args, **kw)
#        manager = get_manager(self.window)
#        if manager.device_stream_manager is not None:
#            self.enabled = True
#
#    def perform(self, event):
#        manager = get_manager(self.window)
#        manager.window = self.window
#        manager.show_device_streamer()


class OpenPyScriptEditorAction(ExtractionLineAction):
    def perform(self, event):
        manager = self._get_manager(event)
        app = event.window.application
        app.open_view(manager.pyscript_editor)


class OpenMultiplexerAction(ExtractionLineAction):
    accelerator = 'Ctrl+Shift+M'

    def __init__(self, *args, **kw):
        super(OpenMultiplexerAction, self).__init__(*args, **kw)
        manager = self._get_manager(None, app=self.window.application)
        if manager.multiplexer_manager is None:
            self.enabled = False

    def perform(self, event):
        manager = self._get_manager(event)
        if manager.multiplexer_manager:
            app = event.window.application
            app.open_view(manager.multiplexer_manager)

#============= EOF ====================================
