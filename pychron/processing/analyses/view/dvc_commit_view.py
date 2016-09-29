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
from pyface.message_dialog import information
from traits.api import HasTraits, Str, Int, Bool, List, Event, Either, Float, on_trait_change
from traitsui.api import View, UItem, VGroup, TabularEditor, HGroup, Item
from traitsui.tabular_adapter import TabularAdapter

from pychron.core.helpers.formatting import floatfmt
from pychron.core.ui.tabular_editor import myTabularEditor
from pychron.dvc.dvc_analysis import analysis_path
from pychron.dvc.tasks.panes import CommitAdapter
from pychron.envisage.icon_button_editor import icon_button_editor
from pychron.envisage.view_util import open_view
from pychron.git_archive.repo_manager import isoformat_date
from pychron.git_archive.utils import get_commits, get_diff, get_head_commit
from pychron.paths import paths
from pychron.pychron_constants import LIGHT_RED, PLUSMINUS_ONE_SIGMA, LIGHT_YELLOW

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
    color_first = Bool(True)

    def get_bg_color(self, obj, trait, row, column=0):
        if self.color_first and row in (0, 1):
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


class BaseDiffView(HasTraits):
    ovalues = List
    values = List
    only_show_diff = Bool(True)

    def __init__(self, record_id, lh, rh, ld, rd, *args, **kw):
        super(BaseDiffView, self).__init__(*args, **kw)

        self.record_id = record_id
        # aj = json.load(d[0].data_stream)
        # bj = json.load(d[1].data_stream)
        # # print 'dddd', d.diff
        # self._load_values(lh, rh, ld, rd, aj, bj)
        self._filter_values()

    @on_trait_change('only_show_diff')
    def _handle_filter_values(self):
        self._filter_values()

    def _diff_value_factory(self, aj, bj, t, k, name):
        a = aj[name]
        b = bj[name]
        if isinstance(a, dict):
            a = a[k]
            b = b[k]

        dv = DiffValue(t, a, b)
        return dv

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


# class TagDiffView(BaseDiffView):
#     base_title = 'Tag'
#
#     def _load_values(self, lh, rh, ld, rd, aj, bj):
#         self.ovalues = [DiffValue('ID', lh, rh, matchable=False),
#                         DiffValue('Date', ld, rd, matchable=False)] + [DiffValue(name, aj[name], bj[name]) for name in
#                                                                        ('name',)]


# class BlanksDiffView(BaseDiffView):
#     base_title = 'Blanks'
#
#     def _load_values(self, lh, rh, ld, rd, aj, bj):
#         blanks = [self._diff_value_factory(aj, bj, t, k, name)
#                   for name in aj.keys()
#                   for t, k in ((name, 'value'), (PLUSMINUS_ONE_SIGMA, 'error'), ('Fit', 'fit'))]
#
#         self.ovalues = [DiffValue('ID', lh, rh, matchable=False),
#                         DiffValue('Date', ld, rd, matchable=False)] + blanks


# class ICFactorDiffView(BlanksDiffView):
#     base_title = 'ICFactor'
#
#
# class IsoEvoDiffView(BlanksDiffView):
#     base_title = 'Iso Evo'


class DiffView(BaseDiffView):
    blanks = List
    icfactors = List
    tags = List
    isoevos = List

    oblanks = List
    oicfactors = List
    otags = List
    oisoevos = List

    def __init__(self, record_id, lh, rh, ld, rd, *args, **kw):
        super(DiffView, self).__init__(record_id, lh, rh, ld, rd, *args, **kw)

        self.record_id = record_id
        # aj = json.load(d.a_blob.data_stream)
        # bj = json.load(d.b_blob.data_stream)
        # print 'dddd', d.diff

        # self._filter_values()

        vs = [DiffValue('ID', lh, rh, matchable=False),
              DiffValue('Date', ld, rd, matchable=False)]
        self.ovalues = vs

    def finish(self):
        self._filter_values()

    def _filter_values(self):
        if self.only_show_diff:
            self.values = [v for v in self.ovalues if not v.match or v.name in ('ID', 'Date')]
            self.blanks = [v for v in self.oblanks if not v.match]
            self.icfactors = [v for v in self.oicfactors if not v.match]
            self.tags = [v for v in self.otags if not v.match]
            self.isoevos = [v for v in self.oisoevos if not v.match]
        else:
            self.values = self.ovalues[:]
            self.blanks = self.oblanks[:]
            self.icfactors = self.oicfactors[:]
            self.tags = self.otags[:]
            self.isoevos = self.oisoevos[:]

    def set_intercepts(self, aj, bj):
        self.oisoevos = [DiffValue(t, aj[name][k], bj[name][k])
                         for name in aj.keys() if name != 'reviewed'
                         for t, k in ((name, 'value'), (PLUSMINUS_ONE_SIGMA, 'error'), ('Fit', 'fit'))]

    def set_blanks(self, aj, bj):
        keys = aj.keys()
        self.oblanks = [DiffValue(t, aj[name][k], bj[name][k])
                        for name in aj.keys() if name != 'reviewed'
                        for t, k in ((name, 'value'), (PLUSMINUS_ONE_SIGMA, 'error'), ('Fit', 'fit'))]

    def set_icfactors(self, aj, bj):
        self.oicfactors = [DiffValue(t, aj[name][k], bj[name][k])
                           for name in aj.keys() if name != 'reviewed'
                           for t, k in ((name, 'value'), (PLUSMINUS_ONE_SIGMA, 'error'), ('Fit', 'fit'))]

    def set_tags(self, aj, bj):
        print 'a', aj
        print 'b', bj
        self.otags = [DiffValue(name, aj[name], bj[name]) for name in ('name',)]

    def traits_view(self):
        v = View(VGroup(HGroup(Item('only_show_diff')),
                        VGroup(UItem('values', editor=TabularEditor(adapter=DiffAdapter(),
                                                                    editable=False),
                                     height=-100)),
                        VGroup(UItem('isoevos', editor=TabularEditor(adapter=DiffAdapter(color_first=False),
                                                                     editable=False),
                                     height=-100),
                               show_border=True, label='Iso Evo',
                               visible_when='isoevos'),
                        VGroup(UItem('blanks', editor=TabularEditor(adapter=DiffAdapter(color_first=False),
                                                                    editable=False),
                                     height=-100),
                               show_border=True, label='Blanks',
                               visible_when='blanks'),
                        VGroup(UItem('icfactors', editor=TabularEditor(adapter=DiffAdapter(color_first=False),
                                                                       editable=False),
                                     height=-100),
                               show_border=True, label='ICFactors',
                               visible_when='icfactors'),
                        VGroup(UItem('tags', editor=TabularEditor(adapter=DiffAdapter(color_first=False),
                                                                  editable=False),
                                     height=-100),
                               show_border=True, label='Tags',
                               visible_when='tags')),

                 title='Diff {}'.format(self.record_id),
                 # title='{} Diff {}'.format(self.base_title, self.record_id),
                 resizable=True,
                 width=500)
        return v


# VIEWS = {'TAG': TagDiffView, 'BLANKS': BlanksDiffView,
#          'ISOEVO': IsoEvoDiffView,
#          'ICFactor': ICFactorDiffView,
#          'COLLECTED': ImportDiffView}


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

        self.repo = Repo(os.path.join(paths.repository_dataset_dir, an.repository_identifier))
        self.record_id = an.record_id
        self.repository_identifier = an.repository_identifier

        self.initialize(an)

    def initialize(self, an):
        pass

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
                self.selected_rhs = get_head_commit(self.repo)
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
            # n = len(self.selected_commits)
            # lhs = self.selected_lhs
            # if n == 1:
            #     rhsid = 'HEAD'
            #     obj = self.repo.head.commit
            #     rhsdate = isoformat_date(obj.committed_date)
            # if lhs.tag == 'IMPORT':
            #     diffs = []
            #     for a in ('blanks', 'icfactors', 'tags', 'intercepts'):
            #         p = analysis_path(self.record_id, self.repository_identifier, modifier=a)
            #         dd = get_diff(self.repo, lhs.hexsha, 'HEAD', p)
            #         if dd:
            #             diffs.append((a, dd))
            #     if diffs:
            #         v = ImportDiffView(self.record_id, lhsid, rhsid, lhsdate, rhsdate)
            #         for a, (aa, bb) in diffs:
            #             func = getattr(v, 'set_{}'.format(a))
            #             func(json.load(aa.data_stream),
            #                  json.load(bb.data_stream))
            #         v.finish()
            #         open_view(v)
            #
            #     return
            # else:
            #     d = get_diff(self.repo, lhs.hexsha, 'HEAD', lhs.path)
            #
            # elif n == 2:
            #     lhs = self.selected_lhs
            #     rhs = self.selected_rhs
            # else:
            #     warning(None, 'Can only diff max of 2')
            #     return

            lhs = self.selected_lhs
            rhs = self.selected_rhs

            lhsid = lhs.hexsha[:8]
            lhsdate = isoformat_date(lhs.date)

            rhsid = rhs.hexsha[:8]
            rhsdate = rhs.date.isoformat()

            diffs = []
            for a in ('blanks', 'icfactors', 'tags', 'intercepts'):
                p = analysis_path(self.record_id, self.repository_identifier, modifier=a)
                dd = get_diff(self.repo, lhs.hexsha, rhs.hexsha, p)
                if dd:
                    diffs.append((a, dd))

            if diffs:
                v = DiffView(self.record_id, lhsid, rhsid, lhsdate, rhsdate)
                for a, (aa, bb) in diffs:
                    func = getattr(v, 'set_{}'.format(a))
                    func(json.load(aa.data_stream),
                         json.load(bb.data_stream))
                v.finish()
                open_view(v)
            else:
                information(None, 'No Differences between {} and {}'.format(lhsid, rhsid))

    def traits_view(self):
        v = View(VGroup(
            icon_button_editor('do_diff', 'edit_diff', tooltip='Make Diff between two commits'),
            UItem('commits', editor=myTabularEditor(adapter=HistoryCommitAdapter(),
                                                    multi_select=True,
                                                    editable=False,
                                                    selected='selected_commits'))))
        return v


class HistoryView(DVCCommitView):
    def initialize(self, an):
        repo = self.repo
        cs = []
        for a, b in (('TAG', 'tag'),
                     ('ISOEVO', 'intercepts'),
                     ('ISOEVO', 'baselines'),
                     ('BLANKS', 'blanks'),
                     ('ICFactor', 'icfactors'),
                     ('IMPORT', ''),
                     ('MANUAL', ''),
                     ('COLLECTION', '')):
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
