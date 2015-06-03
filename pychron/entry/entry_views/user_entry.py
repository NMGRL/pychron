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
from traits.api import Str, List, Enum
from traitsui.api import Item, VGroup, CheckListEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.entry.entry_views.entry import BaseEntry
from pychron.hardware.core.data_helper import make_bitarray


def make_categories(c, av):
    return int(''.join(['1' if ai in c else '0'
                        for ai in av][::-1]), 2)


def parse_categories(cint, av):
    v = map(int, make_bitarray(cint))[::-1]
    cs = [av[i] for i, vi in enumerate(v) if vi]

    return cs


class UserEntry(BaseEntry):
    user = Str
    email = Str
    categories = List
    available_categories = List(['researcher', 'student', 'visitor'])
    affiliation = Str('NMGRL')
    user_style = Enum('simple', 'readonly')
    original_user = Str

    def edit(self, name):
        """
            if name is in database edit else add

        :param name:
        :return:
        """
        db = self.dvc.db
        with db.session_ctx():
            dbuser = db.get_user(name)
            if dbuser:
                self._edit_user(dbuser)
            else:
                self.user = name
                self._add_item(db)

            return self.user

    def _add_item(self, db):
        name = self.user
        if self._add_user_db(db, name):
            return True
        else:
            self.warning_dialog('{} already exists'.format(name))

    def _edit_user(self, dbuser):
        self.info('editing user "{}"'.format(dbuser.name))

        self.user = dbuser.name
        self.original_user = dbuser.name

        self.email = dbuser.email or ''
        self.affiliation = dbuser.affiliation or ''
        self.categories = parse_categories(dbuser.category, self.available_categories)
        info = self.edit_traits()
        if info.result:
            if self.user == self.original_user:
                dbuser.email = self.email
                dbuser.category = make_categories(self.categories, self.available_categories)
                dbuser.affiliation = self.affiliation
            else:
                self._add_item(self.db)

    def _add_user_db(self, db, name):
        if not db.get_user(name):
            c = make_categories(self.categories, self.available_categories)
            db.add_user(name, email=self.email,
                        category=c,
                        affiliation=self.affiliation)
            return True

    def traits_view(self):
        v = self._new_view(

            VGroup(Item('user', style=self.user_style),
                   Item('email'),
                   Item('affiliation'),
                   Item('categories',
                        style='custom',
                        editor=CheckListEditor(name='available_categories', cols=3))))
        return v

# ============= EOF =============================================
#             # db = self.db
    #             # name = self.user
    #             # with db.session_ctx():
    #             # user = db.get_user(self.original_user)
    #             # if user:
    #             #     user.na

    # def add_user(self, user):
    #     db = self.db
    #     with db.session_ctx():
    #         dbuser = db.get_user(user)
    #         print dbuser
    #         if dbuser:
    #             self._edit_user(dbuser)
    #         else:
    #             self.user = user
    #
    #             self._add_user()
    #
    #         return self.user
    #
    # def _add_user(self, ):
    #     self.info('adding user')
    #     db = self.db
    #     name = self.user
    #     if not self._add_user_db(db, name):
    #         while 1:
    #             info = self.edit_traits()
    #             if info.result:
    #
    #                 name = self.user
    #                 if self._add_user_db(db, name):
    #                     break
    #                 else:
    #                     self.warning_dialog('{} already exists'.format(name))
    #                     # with db.session_ctx():
    #                     #     if not db.get_user(name):
    #                     #         c = make_categories(self.categories, self.available_categories)
    #                     #
    #                     #         db.add_user(name, email=self.email,
    #                     #                     category=c,
    #                     #                     affiliation=self.affiliation)
    #                     #         break
    #                     #     else:
    #                     #         self.warning_dialog('{} already exists'.format(name))
    #             else:
    #                 break
    #