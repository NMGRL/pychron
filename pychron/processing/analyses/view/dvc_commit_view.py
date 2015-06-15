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
import json
import os

from git import Repo
from pyface.message_dialog import warning, information
from traits.api import HasTraits, Str, Int, Bool, List, Event
from traitsui.api import View, UItem, VGroup, TabularEditor

# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter
from pychron.dvc.tasks.panes import CommitAdapter
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.git_archive.utils import get_commits, get_diff
from pychron.paths import paths

TAGS = 'TAG', 'BLANK', 'ISOEVO'
TAG_COLORS = {'TAG': '#f5f7c8', 'BLANK': '#cac8f7', 'ISOEVO': '#c8f7e2'}


class HistoryCommitAdapter(CommitAdapter):
    def get_bg_color(self, obj, trait, row, column=0):
        item = getattr(obj, trait)[row]
        color = TAG_COLORS.get(item.tag, 'white')

        return color


class DiffAdapter(TabularAdapter):
    columns = [('Name', 'name'), ('Left', 'lhs'), ('Right', 'rhs')]
    name_width = Int(50)
    lhs_width = Int(100)
    rhs_width = Int(100)


class DiffValue(HasTraits):
    name = Str
    lhs = Str
    rhs = Str
    match = Bool

    def __init__(self, name, lhs, rhs, matchable=True):
        super(DiffValue, self).__init__()
        self.name = name
        self.lhs = lhs
        self.rhs = rhs
        if matchable:
            self.match = lhs == rhs
        else:
            self.match = True


class DiffView(HasTraits):
    pass


class TagDiffView(DiffView):
    values = List

    def __init__(self, record_id, lh, rh, d):
        super(TagDiffView, self).__init__()

        self.record_id = record_id
        aj = json.load(d.a_blob.data_stream)
        bj = json.load(d.b_blob.data_stream)
        print d.diff
        self.values = [DiffValue('ID', lh, rh, matchable=False)] + [DiffValue(name, aj[name], bj[name]) for name in
                                                                    ('name',)]

    def traits_view(self):
        v = View(UItem('values', editor=TabularEditor(adapter=DiffAdapter())),
                 title='Tag Diff {}'.format(self.record_id),
                 resizable=True,
                 width=400)
        return v


class DVCCommitView(HasTraits):
    commits = List
    commit_tag = Str
    do_diff = Event
    selected_commits = List
    commits_func = Str
    modifier = Str
    record_id = Str

    def __init__(self, an, *args, **kw):
        super(DVCCommitView, self).__init__(*args, **kw)

        self.repo = Repo(os.path.join(paths.experiment_dataset_dir, an.experiment_id))
        self.initialize(an)
        self.record_id = an.record_id

    # def initialize(self, an):
    #     path = self._make_path(an)
    #
    #     self.commits = self._get_commits(path, self.commit_tag)
    #     print 'asfd', len(self.commits)
    #     # self.commits = getattr(an, self.commits_func)(self.commit_tag)
    #     # self.commits = an.get_commits(tag='^<{}>'.format(self.commit_tag))

    def _make_path(self, an):
        return an.make_path(self.modifier)

    def _get_commits(self, path, tag=None):
        repo = self.repo
        args = [repo, repo.active_branch.name, path, tag]
        if tag:
            args.append('--grep=^<{}>'.format(tag))

        return get_commits(*args)

    def _do_diff_fired(self):
        print 'asfasfd'
        print self.selected_commits
        if self.selected_commits:
            n = len(self.selected_commits)
            if n == 1:
                lhs = self.selected_commits[0]
                d = get_diff(self.repo, lhs.hexsha, 'HEAD', lhs.path)
                rhsid = 'HEAD'

            elif n == 2:
                lhs, rhs = self.selected_commits
                if lhs.tag != rhs.tag:
                    warning(None, 'Can only compare commits of the same type')
                    return

                rhsid = rhs.hexsha[:8]
                d = get_diff(self.repo, lhs.hexsha, rhs.hexsha, rhs.path)

            else:
                warning(None, 'Can only diff max of 2')
                return

            lhsid = lhs.hexsha[:8]
            if d:
                v = TagDiffView(self.record_id, lhsid, rhsid, d)
                v.edit_traits()
            else:
                information(None, 'No Differences between {} and {}'.format(lhsid, rhsid))

    def traits_view(self):
        v = View(VGroup(
            icon_button_editor('do_diff', 'edit_diff', tooltip='Make Diff between two commits'),
            UItem('commits', editor=TabularEditor(adapter=HistoryCommitAdapter(),
                                                  multi_select=True,
                                                  selected='selected_commits'))))
        return v


class HistoryView(DVCCommitView):
    def initialize(self, an):
        repo = self.repo

        cs = []
        for a, b in (('TAG', 'tag'), ('ISOEVO', 'changeable')):
            path = an.make_path(b)
            args = [repo, repo.active_branch.name, path, a]
            if a:
                args.append('--grep=^<{}>'.format(a))

            css = get_commits(*args)
            for ci in css:
                ci.path = path
            cs.extend(css)

        self.commits = sorted(cs, key=lambda x: x.date, reverse=True)

# class FitsView(DVCCommitView):
#     commit_tag = 'ISOEVO'
#
#
# class BlanksView(DVCCommitView):
#     commit_tag = 'BLANK'


# class TagsView(DVCCommitView):
#     commit_tag = 'TAG'
#     modifier = 'tag'

# ============= EOF =============================================
