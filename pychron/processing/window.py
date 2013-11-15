#===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Instance, Int, Float, Either, Any, Str
from traitsui.api import View, Item
from enable.component_editor import ComponentEditor
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.graph.graph_container import HGraphContainer
from pychron.viewable import Viewable
from traitsui.api import ToolBar, Action
from pyface.image_resource import ImageResource
from pychron.paths import paths
class Window(Viewable):
    container = Instance(HGraphContainer, ())
#    window_width = Either(Int, Float)
#    window_height = Either(Int, Float)
#    window_x = Either(Int, Float)
#    window_y = Either(Int, Float)

#    open_event = Any
    title = Str('  ')
    manager = Any
    def do_edit_analyses(self):
        self.manager.edit_analyses()

    def do_save_pdf(self):
        self.manager.export_figure(kind='pdf')

    def do_save_pdf_table(self):
        self.manager.export_figure_table(kind='pdf')

    def do_save_csv_table(self):
        self.manager.export_figure_table(kind='csv')

    def do_save_excel_table(self):
        self.manager.export_figure_table(kind='excel')

    def traits_view(self):
        tb = ToolBar(
                     Action(name='Edit Analyses',
                            action='do_edit_analyses',
                            image=ImageResource(name='database_edit.png',
                                                search_path=[paths.icons]
                                                )
                            ),
                     Action(name='Save PDF',
                            action='do_save_pdf',
                            image=ImageResource(name='file_pdf.png',
                                                search_path=[paths.icons]
                                                )
                            ),

                     Action(name='Save PDF Table',
                            action='do_save_pdf_table',
                            image=ImageResource(name='table.png',
                                                search_path=[paths.icons]
                                                )
                            ),
                     Action(name='Save CSV Table',
                            action='do_save_csv_table',
                            image=ImageResource(name='csv_text.png',
                                                search_path=[paths.icons]
                                                )
                            ),
                     Action(name='Save Excel Table',
                            action='do_save_excel_table',
                            image=ImageResource(name='excel.png',
                                                search_path=[paths.icons]
                                                )
                            )
                     )

        return self.view_factory(Item('container',
                                      show_label=False, style='custom',
                                     editor=ComponentEditor()),
                                 toolbar=tb
                                 )
#        v = View(,
#                 handler=self.handler_klass,
#                 resizable=True,
#                 width=self.window_width,
#                 height=self.window_height,
#                 x=self.window_x,
#                 y=self.window_y,
#                 title=self.title
#                 )
#        return v
#============= EOF =============================================
