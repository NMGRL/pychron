# ===============================================================================
# Copyright 2015 Jake Ross
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
import os

from traits.api import HasTraits, Button, Str, Any, List
from traitsui.api import View, UItem, HGroup, VGroup, Controller, TabularEditor



# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.editors import TextEditor
from traitsui.tabular_adapter import TabularAdapter


class Conflict(HasTraits):
    path = Str


class MergeModel(HasTraits):
    conflicts = List
    our_text = Str
    their_text = Str

    branch = Str
    remote = Str

    def __init__(self, paths, *args, **kw):
        super(MergeModel, self).__init__(*args, **kw)
        self.conflicts = [Conflict(path=p) for p in paths]

    def set_conflict(self, c):
        repo = self.repo._repo
        ourtext = []
        theirtext = []
        with open(os.path.join(self.repo.path, c.path), 'r') as rfile:
            oflag = False
            tflag = False
            for line in rfile:
                if line.startswith('<<<<<<<'):
                    oflag = True

                elif line.strip() == '=======':
                    oflag = False
                    tflag = True
                elif line.startswith('>>>>>>>'):
                    tflag = False
                elif oflag:
                    ourtext.append(line)
                elif tflag:
                    theirtext.append(line)

        self.our_text = ''.join(ourtext)
        self.their_text = ''.join(theirtext)

        # return
        # cc = repo.rev_parse(ourhexsha)
        # self.left_text = cc.data_stream.read()
        # cc = repo.rev_parse(theirhexsha)
        # self.right_text = cc.data_stream.read()

    def accept_their(self, fl=None):
        self._merge_accept(fl, 'theirs')

    def accept_our(self, fl=None):
        self._merge_accept(fl, 'ours')

    def commit(self):
        self.repo.commit('merged {}/{} with local/{}'.format(self.remote, self.branch, self.branch))

    def _merge_accept(self, fl, k):
        if fl is None:
            fl = self.conflicts

        repo = self.repo._repo
        for fi in fl:
            repo.git.checkout('--{}'.format(k), fi.path)
            self.repo.add(fi.path, commit=False)
            self.conflicts.remove(fi)


class ConflictAdapter(TabularAdapter):
    columns = [('Name', 'path')]


class MergeView(Controller):
    dclicked = Any
    selected = List
    accept_their_button = Button('Accept Their')
    accept_our_button = Button('Accept Our')

    def closed(self, info, is_ok):
        self.model.commit()

    def controller_accept_their_button_changed(self, info):
        if self.selected:
            self.model.accept_their(self.selected)

    def controller_accept_our_button_changed(self, info):
        if self.selected:
            self.model.accept_our(self.selected)

    def controller_dclicked_changed(self, info):
        if self.selected:
            self.model.set_conflict(self.selected[0])

    def traits_view(self):
        cgrp = VGroup(UItem('conflicts', editor=TabularEditor(adapter=ConflictAdapter(),
                                                              operations=[],
                                                              multi_select=True,
                                                              selected='controller.selected',
                                                              dclicked='controller.dclicked')))

        bgrp = VGroup(UItem('controller.accept_our_button'),
                      UItem('controller.accept_their_button'),
                      enabled_when='controller.selected')

        tgrp = HGroup(VGroup(UItem('our_text',
                                   style='custom',
                                   editor=TextEditor(read_only=True)),
                             show_border=True,
                             label='Our'),
                      VGroup(UItem('their_text',
                                   style='custom',
                                   editor=TextEditor(read_only=True)),
                             show_border=True,
                             label='Their'))

        v = View(VGroup(HGroup(cgrp, bgrp),
                        tgrp),
                 buttons=['OK'],
                 title='Merge',
                 resizable=True)
        return v

# ============= EOF =============================================
