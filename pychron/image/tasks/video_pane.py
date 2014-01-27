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
from traits.api import HasTraits, Any, File, String, Int, Enum, Instance, Dict, \
    on_trait_change, Bool, Range
from traitsui.api import View, Item, UItem, EnumEditor
from pyface.tasks.traits_task_pane import TraitsTaskPane
from pyface.tasks.traits_dock_pane import TraitsDockPane

from pychron.canvas.canvas2D.video_canvas import VideoCanvas
from pychron.core.ui.stage_component_editor import VideoComponentEditor

#============= standard library imports ========================
#============= local library imports  ==========================
class Source(HasTraits):
    def url(self):
        return

class LocalSource(Source):
    path = File
    def traits_view(self):
        return View(UItem('path'))

    def url(self):
        return 'file://{}'.format(self.path)

class RemoteSource(Source):
    host = String('localhost', enter_set=True, auto_set=False)
    port = Int(1084, enter_set=True, auto_set=False)
    def traits_view(self):
        return View(
                    Item('host'),
                    Item('port'),

                    )

    def url(self):
        return 'pvs://{}:{}'.format(self.host, self.port)

class ControlsPane(TraitsDockPane):
    name = 'Controls'
    id = 'pychron.video.controls'
    show_grids = Bool(False)
    fps = Range(1, 12, 10)
    quality = Range(1, 75, 10)
    def traits_view(self):
        v = View(
                 Item('show_grids', label='Grid'),
                 Item('fps'),
                 Item('quality')
                 )
        return v

class SourcePane(TraitsDockPane):
    name = 'Source'
    id = 'pychron.video.source'
    kind = Enum('Remote', 'Local')
    source = Instance(Source)
    connections = Dict
    selected_connection = Any

    def traits_view(self):
        v = View(
                 UItem('kind'),
                 UItem('source',
                       style='custom'),
                 UItem('selected_connection',
                       editor=EnumEditor(name='connections'),
                       style='custom'
                       ),
                 )
        return v

    def _kind_changed(self):
        if self.kind == 'Local':
            self.source = LocalSource()
        else:
            self.source = RemoteSource()

    def _source_default(self):
        return RemoteSource()

class BaseVideoPane(HasTraits):
    component = Any
    video = Any
    @on_trait_change('video:fps')
    def _update_fps(self):
        print 'set component fps', self.video.fps
        self.component.fps = self.video.fps

    def _video_changed(self):
        self.component.video = self.video

    def _component_default(self):
        c = VideoCanvas(video=self.video,
                        show_axes=False,
                        show_grids=False,
                        padding=5


                        )
        return c

    def traits_view(self):
        v = View(
                 UItem('component',
                       style='custom',
                       editor=VideoComponentEditor()
                       )
                 )
        return v

class VideoPane(TraitsTaskPane, BaseVideoPane):
    pass

class VideoDockPane(TraitsDockPane, BaseVideoPane):
    id = 'pychron.video'
    name = 'Video'
#============= EOF =============================================
