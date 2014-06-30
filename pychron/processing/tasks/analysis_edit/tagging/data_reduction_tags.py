#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
from traits.api import HasTraits, Str, Button
from traitsui.api import View, Item, UItem

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.processing.tasks.analysis_edit.tagging.base_tags import BaseTagModel


class DataReductionTagModel(BaseTagModel):
    tagname = Str
    comment = Str
    edit_comment_button = Button('Comment')

    def _edit_comment_button_fired(self):
        self.edit_traits(view='edit_comment_view')

    def edit_comment_view(self):
        v=View(UItem('comment', style='custom'),
               kind='livemodal', buttons=['OK','Cancel'],
               title='Comment')
        return v
#============= EOF =============================================

