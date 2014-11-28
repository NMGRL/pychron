# ===============================================================================
# Copyright 2014 Jake Ross
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
from traits.api import Str, Button, HasTraits, List, Long
from traitsui.api import View, UItem

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.tagging.base_tags import BaseTagModel


class DataReductionTag(HasTraits):
    name = Str
    create_date = Str
    comment = Str
    analyses = List
    id = Long

class SelectDataReductionTagModel(HasTraits):
    tags = List
    otags = List

    selected = DataReductionTag
    user_filter = Str
    name_filter = Str

    def _user_filter_changed(self, new):
        tags =self._filter('name', self.name_filter, self.otags)
        self.tags = self._filter('user', new, tags)

    def _name_filter_changed(self, new):
        tags = self._filter('name', new, self.otags)
        self.tags = self._filter('user', self.user_filter, tags)

    def _filter(self, attr, val, tags):
        return [ti for ti in tags if getattr(ti, attr).startswith(val)] if val else tags

    def load_tags(self, dbtags):
        def g():
            for di in dbtags:
                d = DataReductionTag(name=di.name,
                                     id = di.id,
                                     create_date=di.create_date.strftime('%m-%d-%Y'),
                                     user=di.user.name,
                                     comment=di.comment or '')
                yield d
        self.otags = self.tags = list(g())


class DataReductionTagModel(BaseTagModel):
    tagname = Str
    comment = Str
    edit_comment_button = Button('Comment')

    def _edit_comment_button_fired(self):
        self.edit_traits(view='edit_comment_view')

    def edit_comment_view(self):
        v = View(UItem('comment', style='custom'),
                 kind='livemodal', buttons=['OK', 'Cancel'],
                 title='Comment')
        return v


# ============= EOF =============================================

