# ===============================================================================
# Copyright 2014 Jake Ross
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

# ============= enthought library imports =======================
from datetime import datetime

from traits.api import HasTraits, Str, Date
from traitsui.api import View, UItem

# ============= standard library imports ========================
import os
# ============= local library imports  ==========================


class NewNameView(HasTraits):
    name = Str
    message = Str
    title = Str

    def traits_view(self):
        v = View(UItem('message', style='readonly', width=1.0),
                 UItem('name'),
                 title=self.title,
                 width=300,
                 buttons=['OK', 'Cancel'])
        return v


class PostView(HasTraits):
    low_post = Date
    high_post = Date

    @property
    def posts(self):
        return self.low_post, self.high_post

    def traits_view(self):
        v = View(UItem('low_post', style='custom'),
                 UItem('high_post', style='custom'),
                 title='Select Date Range',
                 width=500,
                 buttons=['OK', 'Cancel'])
        return v


def get_posts(post_view, chron):
    if not post_view:
        pv = PostView()
        l, h = chron[-1], chron[0]
        fmt = '%m-%d-%Y %H:%M:%S'
        pv.low_post = datetime.strptime(l.create_date, fmt)
        pv.high_post = datetime.strptime(h.create_date, fmt)
        post_view = pv

    info = post_view.edit_traits(kind='livemodal')
    if info.result:
        return post_view, post_view.posts
    else:
        return post_view, None


def get_new_name(root, test, title, name=''):
    e = NewNameView(title=title, name=name)
    while 1:
        info = e.edit_traits(kind='livemodal')
        if info.result:
            # e=e.name.replace(' ','_')
            en = e.name
            p = os.path.join(root, en)
            if not test(p):
                return p
            else:
                e.message = '{} already exists'.format(en)
        else:
            break

# ============= EOF =============================================



