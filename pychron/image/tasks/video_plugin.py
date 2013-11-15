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
from traits.api import HasTraits, List
from traitsui.api import View, Item
from pychron.envisage.tasks.base_task_plugin import BaseTaskPlugin
from envisage.ui.tasks.task_factory import TaskFactory
from pychron.image.tasks.video_task import VideoTask
from envisage.extension_point import ExtensionPoint
#============= standard library imports ========================
#============= local library imports  ==========================

class VideoPlugin(BaseTaskPlugin):

    '''
        a list of name, url (file:///abs/path or pvs://host[:port=8080]) tuples
        
        if file then should be a path to an image
        if pvs than should be address to a Pychron Video Server
    '''
    id = 'pychron.video'
    sources = ExtensionPoint(List,
                                   id='pychron.video.sources'
                            )


    def _tasks_default(self):
        ts = [TaskFactory(id='pychron.video',
                          name='Video Display',
                          factory=self._video_task_factory,
                          task_group='hardware'
                         )]
        return ts

    def _video_task_factory(self):
        t = VideoTask(
                      available_connections=self.sources
                      )
        return t
#         elm = self.application.get_service(ExtractionLineManager)
#         t = ExtractionLineTask(manager=elm)
#         return t
#============= EOF =============================================
