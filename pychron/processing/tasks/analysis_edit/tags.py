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
from traits.etsconfig.etsconfig import ETSConfig

ETSConfig.toolkit = 'qt4'

from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn


#============= enthought library imports =======================
from traits.api import HasTraits, Str, List, Instance, Any, Button, Date, Bool
from traitsui.api import View, Item, UItem, ButtonEditor, HGroup, TableEditor, Handler, VGroup
from pychron.loggable import Loggable
from pychron.paths import paths
from pyface.image_resource import ImageResource

#============= standard library imports ========================
#============= local library imports  ==========================

class Tag(HasTraits):
    name = Str
    user = Str
    date = Date
    omit_ideo = Bool
    omit_spec = Bool
    omit_iso = Bool


class TagTable(HasTraits):
    tags = List
    db = Any

    def load(self):
        db = self.db
        with db.session_ctx():
            dbtags = db.get_tags()

            invalid_tag = next((t for t in dbtags
                                if t.name == 'invalid'), None)
            if invalid_tag:
                dbtags.remove(invalid_tag)
                tags = [invalid_tag, ] + dbtags
            else:
                tags = dbtags

            ts = [Tag(name=di.name,
                      user=di.user,
                      date=di.create_date,
                      omit_ideo=di.omit_ideo or False,
                      omit_iso=di.omit_iso or False,
                      omit_spec=di.omit_spec or False)
                  for di in tags]

            self.tags = ts

    def _add_tag(self, tag):
        name, user = tag.name, tag.user
        db = self.db
        with db.session_ctx():
            return db.add_tag(name=name, user=user,
                              omit_ideo=tag.omit_ideo,
                              omit_spec=tag.omit_spec,
                              omit_iso=tag.omit_iso)

    def add_tag(self, tag):
        self._add_tag(tag)
        self.load()

    def delete_tag(self, tag):
        if isinstance(tag, str):
            tag = next((ta for ta in self.tags if ta.name == tag), None)
            print tag

        if tag:
            self.tags.remove(tag)
            db = self.db
            with db.session_ctx():
                db.delete_tag(tag.name)

    def save(self):
        db = self.db
        with db.session_ctx():
            for ti in self.tags:
                dbtag = db.get_tag(ti.name)
                if dbtag is None:
                    dbtag = self._add_tag(ti)

                for a in ('ideo', 'spec', 'iso'):
                    a = 'omit_{}'.format(a)
                    setattr(dbtag, a, getattr(ti, a))


#class TagAdapter(TabularAdapter):
#    columns = [('Name', 'name'), ('User', 'user'),
#               ('Date', 'date')
#               ]
class TagTableViewHandler(Handler):
    def closed(self, info, isok):
        if isok:
            info.object.save()


class TagTableView(Loggable):
    table = Instance(TagTable, ())
    add_tag_button = Button
    delete_tag_button = Button
    save_button = Button

    selected = Any

    def save(self):
        self.table.save()

    def _save_button_fired(self):
        self.save()
        self.information_dialog('Changes saved to database')

    def _add_tag_button_fired(self):
        n = Tag()
        tag_view = View(
            VGroup(
                HGroup(Item('name'),
                       #Label('optional'),
                       Item('user')),
                HGroup(
                    Item('omit_ideo',
                         label='Ideogram'),
                    Item('omit_spec',
                         label='Spectrum'),
                    Item('omit_iso',
                         label='Isochron'),
                    show_border=True,
                    label='Omit'
                ),
            ),
            buttons=['OK', 'Cancel'],
            title='Add Tag'
        )
        info = n.edit_traits(kind='livemodal', view=tag_view)
        if info.result:
            self.table.add_tag(n)

    def _delete_tag_button_fired(self):
        s = self.selected
        if s:
            if not isinstance(s, list):
                s = (s,)
            for si in s:
                self.table.delete_tag(si)

    def traits_view(self):
        cols = [ObjectColumn(name='name'),
                ObjectColumn(name='user'),
                CheckboxColumn(name='omit_ideo'),
                CheckboxColumn(name='omit_spec'),
                CheckboxColumn(name='omit_iso')]

        editor = TableEditor(columns=cols,
                             selected='selected',
                             sortable=False)

        v = View(UItem('object.table.tags',
                       editor=editor),
                 HGroup(
                     UItem('add_tag_button',
                           style='custom',
                           tooltip='Add a tag',
                           editor=ButtonEditor(image=ImageResource(name='add.png',
                                                                   search_path=paths.icon_search_path))
                     ),
                     UItem('delete_tag_button',
                           style='custom',
                           tooltip='Delete selected tags',
                           editor=ButtonEditor(image=ImageResource(name='delete.png',
                                                                   search_path=paths.icon_search_path))
                     ),
                     UItem('save_button',
                           style='custom',
                           tooltip='Save changes to the database',
                           editor=ButtonEditor(image=ImageResource(name='database_save.png',
                                                                   search_path=paths.icon_search_path))
                     ),


                 ),

                 resizable=True,
                 width=500,
                 height=400,
                 buttons=['OK', 'Cancel'],
                 kind='livemodal',
                 handler=TagTableViewHandler,
                 title='Tags'
        )
        return v


if __name__ == '__main__':
    t = TagTableView()
    t.table.tags = [Tag(name='foo') for i in range(10)]
    t.configure_traits()
#============= EOF =============================================
