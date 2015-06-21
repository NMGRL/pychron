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
from pyface.message_dialog import warning, information
from traits.api import HasTraits, Str, Int, Bool, List, Event, Either, Float, on_trait_change
from traitsui.api import View, UItem, VGroup, TabularEditor, HGroup, Item
from traitsui.tabular_adapter import TabularAdapter
# ============= standard library imports ========================
import json
import os
from git import Repo
# ============= local library imports  ==========================
from pychron.core.helpers.formatting import floatfmt
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.dvc.tasks.panes import CommitAdapter
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.view_util import open_view
from pychron.git_archive.repo_manager import isoformat_date
from pychron.git_archive.utils import get_commits, get_diff
from pychron.paths import paths
from pychron.pychron_constants import LIGHT_RED, PLUSMINUS_SIGMA, LIGHT_YELLOW

TAGS = 'TAG', 'BLANK', 'ISOEVO', 'ICFactor'
TAG_COLORS = {'TAG': '#f5f7c8', 'BLANKS': '#cac8f7',
              'ISOEVO': '#c8f7e2', 'IMPORT': '#FAE8F0',
              'ICFactor': '#D2D4A7'}


class HistoryCommitAdapter(CommitAdapter):
    def get_bg_color(self, obj, trait, row, column=0):
        item = getattr(obj, trait)[row]
        color = TAG_COLORS.get(item.tag, 'white')

        return color


class DiffAdapter(TabularAdapter):
    columns = [('Name', 'name'), ('First', 'lhs'), ('Second', 'rhs'), ('Dev %', 'dev')]
    name_width = Int(50)
    lhs_width = Int(150)
    rhs_width = Int(150)

    def get_bg_color(self, obj, trait, row, column=0):
        if row in (0, 1):
            return LIGHT_YELLOW

        if not obj.only_show_diff:
            item = getattr(obj, trait)[row]
            return LIGHT_RED if not item.match else 'white'
        else:
            return 'white'


class DiffValue(HasTraits):
    name = Str
    lhs = Either(Str, Float)
    rhs = Either(Str, Float)
    match = Bool
    dev = Str

    def __init__(self, name, lhs, rhs, matchable=True, tol=1e-10):
        super(DiffValue, self).__init__()
        self.name = name
        self.lhs = lhs
        self.rhs = rhs
        if matchable:
            if isinstance(lhs, float):
                self.match = abs(lhs - rhs) < tol
                try:
                    dev = (rhs - lhs) / lhs * 100
                    dev = floatfmt(dev)
                except ZeroDivisionError:
                    dev = 'NaN'
                self.dev = dev
            else:
                self.match = lhs == rhs
        else:
            self.match = True


class DiffView(HasTraits):
    ovalues = List
    values = List
    only_show_diff = Bool(True)

    def __init__(self, record_id, lh, rh, ld, rd, d, *args, **kw):
        super(DiffView, self).__init__(*args, **kw)

        self.record_id = record_id
        aj = json.load(d.a_blob.data_stream)
        bj = json.load(d.b_blob.data_stream)
        # print 'dddd', d.diff
        self._load_values(lh, rh, ld, rd, aj, bj)
        self._filter_values()

    @on_trait_change('only_show_diff')
    def _filter_values(self):
        if self.only_show_diff:
            self.values = [v for v in self.ovalues if not v.match or v.name in ('ID', 'Date')]
        else:
            self.values = self.ovalues[:]

    def traits_view(self):
        v = View(VGroup(HGroup(Item('only_show_diff'))),

                 UItem('values', editor=TabularEditor(adapter=DiffAdapter(),
                                                      editable=False)),
                 title='{} Diff {}'.format(self.base_title, self.record_id),
                 resizable=True,
                 width=500)
        return v


class TagDiffView(DiffView):
    base_title = 'Tag'

    def _load_values(self, lh, rh, ld, rd, aj, bj):
        self.ovalues = [DiffValue('ID', lh, rh, matchable=False),
                        DiffValue('Date', ld, rd, matchable=False)] + [DiffValue(name, aj[name], bj[name]) for name in
                                                                       ('name',)]


class BlanksDiffView(DiffView):
    base_title = 'Blanks'

    def _load_values(self, lh, rh, ld, rd, aj, bj):
        # print aj
        # print bj
        blanks = [DiffValue(t, aj[name][k], bj[name][k])
                  for name in aj.keys()
                  for t, k in ((name, 'value'), (PLUSMINUS_SIGMA, 'error'), ('Fit', 'fit'))]

        self.ovalues = [DiffValue('ID', lh, rh, matchable=False),
                        DiffValue('Date', ld, rd, matchable=False)] + blanks


class ICFactorDiffView(BlanksDiffView):
    base_title = 'ICFactor'


VIEWS = {'TAG': TagDiffView, 'BLANKS': BlanksDiffView, 'ICFactor': ICFactorDiffView}


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

    def _selected_commits_changed(self, new):
        if new:
            if len(new) == 1:
                self.selected_lhs = new[0]
                self.selected_rhs = 'HEAD'
            elif len(new) == 2:
                a, b = new
                self.selected_rhs = a if b == self.selected_lhs else b

    def _make_path(self, an):
        return an.make_path(self.modifier)

    def _get_commits(self, path, tag=None):
        repo = self.repo
        args = [repo, repo.active_branch.name, path, tag]
        if tag:
            args.append('--grep=^<{}>'.format(tag))

        return get_commits(*args)

    def _do_diff_fired(self):
        if self.selected_commits:
            n = len(self.selected_commits)

            lhs = self.selected_lhs
            lhsdate = isoformat_date(lhs.date)
            if n == 1:
                d = get_diff(self.repo, lhs.hexsha, 'HEAD', lhs.path)
                rhsid = 'HEAD'
                obj = self.repo.head.commit
                rhsdate = isoformat_date(obj.committed_date)

            elif n == 2:
                lhs = self.selected_lhs
                rhs = self.selected_rhs
                # lhs, rhs = self.selected_commits
                if lhs.tag != rhs.tag:
                    warning(None, 'Can only compare commits of the same type')
                    return

                rhsid = rhs.hexsha[:8]
                rhsdate = rhs.date.isoformat()
                d = get_diff(self.repo, lhs.hexsha, rhs.hexsha, rhs.path)

            else:
                warning(None, 'Can only diff max of 2')
                return

            lhsid = lhs.hexsha[:8]
            if d:
                # if lhs.tag=='TAG':
                klass = VIEWS[lhs.tag]
                v = klass(self.record_id, lhsid, rhsid, lhsdate, rhsdate, d)

                open_view(v)
                # v.edit_traits()
            else:
                information(None, 'No Differences between {} and {}'.format(lhsid, rhsid))

    def traits_view(self):
        v = View(VGroup(
            icon_button_editor('do_diff', 'edit_diff', tooltip='Make Diff between two commits'),
            UItem('commits', editor=myTabularEditor(adapter=HistoryCommitAdapter(),
                                                    multi_select=True,
                                                    selected='selected_commits'))))
        return v


class HistoryView(DVCCommitView):
    def initialize(self, an):
        repo = self.repo

        cs = []
        for a, b in (('TAG', 'tag'), ('ISOEVO', 'intercepts'),
                     ('BLANKS', 'blanks'),
                     ('ICFactor', 'icfactors'),
                     ('IMPORT', '')):
            path = an.make_path(b)
            if path:
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
