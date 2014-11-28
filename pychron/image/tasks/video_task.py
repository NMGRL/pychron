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

#============= enthought library imports =======================
from traits.api import Instance, on_trait_change, List

from pyface.tasks.task_layout import PaneItem, TaskLayout, Splitter
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.base_task import BaseManagerTask
from pychron.image.tasks.video_pane import VideoPane, SourcePane, ControlsPane
from pychron.image.video_source import VideoSource, parse_url


class VideoTask(BaseManagerTask):
    id = 'pychron.extraction_line'
    name = 'Video Display'
    video_source = Instance(VideoSource, ())
    source_pane = Instance(SourcePane)
    controls_pane = Instance(ControlsPane)
    available_connections = List

    def _default_layout_default(self):
        return TaskLayout(
#                           top=PaneItem('pychron.extraction_line.gauges'),
                        left=Splitter(
                                      PaneItem('pychron.video.source'),
                                      PaneItem('pychron.video.controls'),
                                      orientation='vertical'
                                      ),

#                          width=500,
#                          height=500
                          )

    def new_video_dock_pane(self, video=None):
        from pychron.image.tasks.video_pane import VideoDockPane
        if video is None:
            video = self.video_source

        return VideoDockPane(video=video)

    def prepare_destroy(self):
        pass

    def create_central_pane(self):
        self.video_pane = VideoPane(
                                    video=self.video_source,

                                    )

        return self.video_pane

    def create_dock_panes(self):
        self.source_pane = SourcePane(
                                      connections=dict(self.available_connections)
                                      )

        self.controls_pane = ControlsPane()
        self.video_source.set_url(self.source_pane.source.url())
        panes = [
                 self.source_pane,
                 self.controls_pane
                 ]
        return panes

    @on_trait_change('controls_pane:[show_grids,fps, quality]')
    def _update_control(self, name, new):
        if name == 'show_grids':
            self.video_pane.component.show_grids = new
        elif name == 'fps':
            self.video_pane.component.fps = new
        elif name == 'quality':
            self.video_source.quality = new

    @on_trait_change('source_pane:[selected_connection, source:+]')
    def _update_source(self, name, new):
        if name == 'selected_connection':
            islocal, r = parse_url(new)
            if islocal:
                pass
            else:
                self.source_pane.source.host = r[0]
                self.source_pane.source.port = r[1]
        else:
            url = self.source_pane.source.url()

            self.video_source.set_url(url)
#         if name == 'source':
#             self.video_source.image_path = new

#     @on_trait_change('video_source:fps')
#     def _update_fps(self):
#         self.video_pane.set_fps(self.video_source.fps)
# ============= EOF =============================================
