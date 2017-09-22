# ===============================================================================
# Copyright 2017 ross
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
import StringIO
import os
from zipfile import ZipFile

from PIL import Image
from traits.api import HasTraits, List, Any, Str, Button, Int, Property, Instance, Long, Event
from traitsui.api import View, UItem, HGroup, VGroup, HSplit, spring, TabularEditor
from traitsui.tabular_adapter import TabularAdapter

from pychron.core.helpers.filetools import add_extension
from pychron.core.ui.image_editor import ImageEditor
from pychron.envisage.icon_button_editor import icon_button_editor


class ImageRecordAdapter(TabularAdapter):
    columns = [('Name', 'name'),
               ('Note', 'note')]


class ImageRecord(HasTraits):
    path = Str
    note = Str
    id  = Long

    @property
    def name(self):
        return os.path.basename(self.path)

    def traits_view(self):
        v = View(VGroup(UItem('note', style='custom'),
                        label='Note', show_border=True),
                 buttons=['OK', 'Cancel'],
                 title='Edit Image Note',
                 resizable=True)
        return v


class ImageViewer(HasTraits):
    image_getter = None
    records = List(ImageRecord)
    selected_image = Any
    # selected_image_name = Instance(ImageRecord)
    selected_record = Instance(ImageRecord)
    image_names = List
    nimages = Int

    next_button = Button
    first_button = Button
    last_button = Button
    previous_button = Button
    save_button = Button
    save_zip_button = Button
    counter = Int(-1)
    display_counter = Property(depends_on='counter')

    next_enabled = Property(depends_on='counter')
    previous_enabled = Property(depends_on='counter')
    title = Str
    edit_event = Any
    dclicked = Event
    dclicked_enabled=False

    def _get_next_enabled(self):
        return self.counter < self.nimages - 1

    def _get_previous_enabled(self):
        return self.counter > 0

    def _get_display_counter(self):
        return self.counter + 1

    def set_images(self, records):

        self.records = [ImageRecord(path=p, note=n or '', id=i) for p, n, i in records]
        # self.images = paths
        self.nimages = len(records)
        self.image_names = [i.name for i in self.records]
        self.counter = 0

    def _next_button_fired(self):
        self.counter += 1

    def _previous_button_fired(self):
        self.counter -= 1

    def _last_button_fired(self):
        self.counter = self.nimages - 1

    def _first_button_fired(self):
        self.counter = 0

    def _save_button_fired(self):
        from pyface.file_dialog import FileDialog
        dialog = FileDialog(action='save as',
                            default_directory=os.path.join(os.path.expanduser('~')))

        from pyface.constant import OK
        if dialog.open() == OK:
            path = dialog.path
            if path:
                self.selected_image.save(add_extension(path, '.jpg'))

    def _save_zip_button_fired(self):
        from pyface.file_dialog import FileDialog
        dialog = FileDialog(action='save as',
                            default_directory=os.path.join(os.path.expanduser('~')))

        from pyface.constant import OK
        if dialog.open() == OK:
            path = dialog.path
            if path:
                with ZipFile(add_extension(path, '.zip'), 'w') as zipf:
                    for p in self.image_names:
                        buf = self._get_image_buf(p)
                        if buf:
                            zipf.writestr(p, buf.getvalue())
                            # self.selected_image.save(path)

    def _counter_changed(self):
        self.selected_record = self.records[self.counter]

    def _dclicked_fired(self):
        if self.dclicked_enabled:
            info = self.selected_record.edit_traits(kind='livemodal')
            if info.result:
                self.edit_event = self.selected_record

    def traits_view(self):
        ctrl_grp = HGroup(HGroup(icon_button_editor('first_button', 'go-first', tooltip='First'),
                                 icon_button_editor('previous_button', 'go-previous',
                                                    enabled_when='previous_enabled', tooltip='Previous'),
                                 icon_button_editor('next_button', 'go-next', enabled_when='next_enabled',
                                                    tooltip='Next'),
                                 icon_button_editor('last_button', 'go-last', tooltip='Last'),
                                 defined_when='nimages'),
                          spring,
                          icon_button_editor('save_button', 'picture-save', tooltip='Save to File'),
                          icon_button_editor('save_zip_button', 'compress', tooltip='Compress/Save all images',
                                             defined_when='nimages'))

        v = View(HSplit(VGroup(ctrl_grp,
                               UItem('records',
                                     editor=TabularEditor(adapter=ImageRecordAdapter(),
                                                          editable=False,
                                                          dclicked='dclicked',
                                                          selected='selected_record'),
                                     # editor=ListStrEditor(horizontal_lines=True,
                                     #                      editable=False,
                                     #                      selected='selected_image_name'),
                                     defined_when='nimages')),
                        UItem('selected_image',
                              width=1.0,
                              height=1.0,
                              editor=ImageEditor())),
                 title=self.title,
                 resizable=True)
        return v

    def _selected_record_changed(self, new):
        if new:
            buf = self._get_image_buf(new.path)
            # buf.seek(0)
            img = Image.open(buf)
            self.selected_image = img.convert('RGBA')

    def _get_image_buf(self, path):
        # path = next((p.path for p in self.records if p.name == path), None)
        if path:
            buf = StringIO.StringIO()
            self.image_getter.get(path, buf)
            buf.seek(0)
            return buf

# ============= EOF =============================================
