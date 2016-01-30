# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from chaco.api import ArrayPlotData, Plot, HPlotContainer
from chaco.tools.api import ZoomTool, PanTool
from chaco.tools.image_inspector_tool import ImageInspectorOverlay, \
    ImageInspectorTool
from enable.component import Component
from enable.component_editor import ComponentEditor
from traits.api import HasTraits, Instance, List, Str, Bool, on_trait_change, String, \
    Button, Dict, Any
from traitsui.api import View, Item, ListStrEditor, HGroup, VGroup, \
    spring, VSplit, Group

# ============= standard library imports ========================
import Image
from numpy import array
import os
import httplib
# ============= local library imports  ==========================
from pychron.core.ui.custom_label_editor import CustomLabel
from pychron.database.isotope_database_manager import IsotopeDatabaseManager
from pychron.paths import paths

PORT = 8083
# TEST_IMAGE = Image.open(open('/Users/ross/Sandbox/snapshot001.jpg'))
# TEST_IMAGE = ImageData.fromfile('/Users/ross/Sandbox/foo.png')
class ImageContainer(HasTraits):
    container = Instance(HPlotContainer, ())
    name = String
    def traits_view(self):
        v = View(VGroup(
                        HGroup(spring, CustomLabel('name', color='maroon', size=16,
                                                   height=-25,
                                                   width=100,
                                                   ), spring),
                        Item('container', show_label=False, editor=ComponentEditor()),
                 ))
        return v

class ImageSpec(HasTraits):
    name = Str
    note = Str
    def traits_view(self):
        v = View(VGroup(Item('name'),
                        Group(
                              Item('note', style='custom', show_label=False),
                              show_border=True,
                              label='Note'
                              )
                        )
               )
        return v

class ImageEditor(HasTraits):
    names = List
    selected = Str
    save_db = Button('Save to DB')
    image_spec = Instance(ImageSpec)
    image_specs = Dict

    db = Any
# ===============================================================================
# handlers
# ===============================================================================
    def _selected_changed(self):
        if self.selected in self.image_specs:
            spec = self.image_specs[self.selected]
        else:
            spec = ImageSpec(name=self.selected)
            self.image_specs[self.selected] = spec

        self.image_spec = spec

    def _save_db_fired(self):
        db = self.db
        print db

    def traits_view(self):
        v = View(
                 VSplit(
                     Item('names', show_label=False,
                          editor=ListStrEditor(editable=False,
                                                selected='selected',
                                                operations=[]
                                                ),
                          height=0.6
                          ),
                     Item('image_spec', show_label=False, style='custom',
                          height=0.4
                          )
                     ),
                 Item('save_db', show_label=False)
                 )
        return v

class ImageBrowser(IsotopeDatabaseManager):

#    db = Instance(IsotopeAdapter)

    image_container = Instance(ImageContainer, ())
    image_editor = Instance(ImageEditor)
    plot = Instance(Component)
#    names = List
#    selected = Str

    use_cache = Bool(True)
    cache_dir = paths.image_cache_dir

    _conn = None
    def _image_editor_default(self):
        im = ImageEditor(db=self.db)
        return  im

    def _is_cached(self, p):
        p = os.path.join(self.cache_dir, p)
        return os.path.isfile(p)


    def load_from_remote_source(self, name):
        if self._is_cached(name):
            data = self._get_cached(name)
        else:
            data = self._get_remote_file(name)

        self._load_image_data(data)

    def load_remote_directory(self, name):
        self.info('retrieve contents of remote directory {}'.format(name))

        resp = self._get(name)
        if resp:
            htxt = resp.read()
            for li in htxt.split('\n'):
                if li.startswith('<li>'):
                    args = li[4:].split('>')
                    name, _tail = args[1].split('<')
                    self.image_editor.names.append(name)

            return True

    def _connection_factory(self, reset=False):
        if reset or self._conn is None:
            host, port = 'localhost', 8081
            url = '{}:{}'.format(host, port)
            conn = httplib.HTTPConnection(url)
        else:
            conn = self._conn

        self._conn = conn
        return conn

#    def _get(self, name):
#        conn = self._connection_factory()
#        conn.request('GET', '/{}'.format(name))
#        return conn.getresponse()

#    def _get_remote_file(self, name):
#        self.info('retrieve {} from remote directory'.format(name))
#        resp = self._get(name)
#
#        buf = StringIO()
#        buf.write(resp.read())
#        buf.seek(0)
#        im = Image.open(buf)
#        im = im.convert('RGB')
#
#        if self.use_cache:
#            buf.seek(0)
#            if os.path.isdir(self.cache_dir):
#                with open(os.path.join(self.cache_dir, name), 'w') as fp:
#                    fp.write(buf.read())
#            else:
#                self.info('cache directory does not exist. {}'.format(self.cache_dir))
#
#        buf.close()
#
#        return array(im)

    def _get_cached(self, name):
        self.info('retrieve {} from cache directory'.format(name))
        p = os.path.join(self.cache_dir, name)
        with open(p, 'r') as rfile:
            im = Image.open(rfile)
            im = im.convert('RGB')
            return array(im)

    def _load_image_data(self, data):
        cont = HPlotContainer()
        pd = ArrayPlotData()
        plot = Plot(data=pd, padding=[30, 5, 5, 30], default_origin='top left')

        pd.set_data('img', data)
        img_plot = plot.img_plot('img',
                                 )[0]

        self._add_inspector(img_plot)
        self._add_tools(img_plot)

        cont.add(plot)
        cont.request_redraw()
        self.image_container.container = cont

    def _add_inspector(self, img_plot):
        imgtool = ImageInspectorTool(img_plot)
        img_plot.tools.append(imgtool)
        overlay = ImageInspectorOverlay(component=img_plot, image_inspector=imgtool,
                                        bgcolor="white", border_visible=True)

        img_plot.overlays.append(overlay)
#
    def _add_tools(self, img_plot):
        zoom = ZoomTool(component=img_plot, tool_mode="box", always_on=False)
        pan = PanTool(component=img_plot, restrict_to_data=True)
        img_plot.tools.append(pan)

        img_plot.overlays.append(zoom)


# ===============================================================================
# handlers
# ===============================================================================
    @on_trait_change('image_editor:selected')
    def _selected_changed(self):
        sel = self.image_editor.selected
        if sel:
            self.load_from_remote_source(sel)
            self.image_container.name = sel

    def traits_view(self):
        v = View(
                HGroup(
                    Item('image_editor', show_label=False, style='custom',
                         width=0.3
                         ),

#                    Item('names', show_label=False, editor=ListStrEditor(editable=False,
#                                                                         selected='selected',
#                                                                         operations=[]
#                                                                         ),
#                         width=0.3,
#                         ),
                    Item('image_container', style='custom',
                         width=0.7,
                         show_label=False)
                       ),
#                    Item('container', show_label=False,
#                         width=0.7,
#                       editor=ComponentEditor())),
                 resizable=True,
                 height=800,
                 width=900
                 )
        return v


if __name__ == '__main__':
    from pychron.core.helpers.logger_setup import logging_setup
    logging_setup('image_viewer')
    im = ImageBrowser(cache_dir='/Users/ross/Sandbox/cache')
    im.load_remote_directory('')
#    im.load_from_remote_source('raster2.png')
#    im.load_remote_directory()
#    im.names = 'snapshot001.jpg,snapshot002.jpg,snapshot003.jpg,snapshot004.jpg'.split(',')
#    im.load_from_remote_source('foo')
#    im.load_image_from_file('/Users/ross/Sandbox/diodefailsnapshot.jpg')
    im.configure_traits()
# ============= EOF =============================================
