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
from traits.api import HasTraits, Str, Any, Int, Property
from traitsui.api import View, UItem, TextEditor, Item, VGroup
# ============= standard library imports ========================
# ============= local library imports  ==========================
from traitsui.tabular_adapter import TabularAdapter

from pychron.core.helpers.traitsui_shortcuts import okcancel_view

# logsep = chr(0x01)
logsep = '$'

class StatusView(HasTraits):
    def traits_view(self):
        v = View(UItem('status', style='custom',
                       editor=TextEditor(read_only=True)),
                 kind='modal',
                 title='Repository Status',
                 width=500,
                 resizable=True)
        return v


class NewTagView(HasTraits):
    message = Str
    name = Str

    def traits_view(self):
        v = okcancel_view(VGroup(Item('name'),
                                 VGroup(UItem('message', style='custom'),
                                        show_border=True, label='Message')),
                          width=400,
                          title='New Tag')

        return v


class NewBranchView(HasTraits):
    name = Property(depends_on='_name')
    branches = Any
    _name = Str

    def traits_view(self):
        v = okcancel_view(UItem('name'),
                          width=200,
                          title='New Branch')
        return v

    def _get_name(self):
        return self._name

    def _set_name(self, v):
        self._name = v

    def _validate_name(self, v):
        if v not in self.branches:
            if ' ' not in v:
                return v


class GitObjectAdapter(TabularAdapter):
    hexsha_width = Int(80)
    message_width = Int(300)
    date_width = Int(120)

    font = '10'
    hexsha_text = Property
    message_text = Property

    def _get_hexsha_text(self):
        return self.item.hexsha[:8]

    def _get_message_text(self):
        return self._truncate_message(self.item.message)

    def _truncate_message(self, m):
        if len(m) > 200:
            m = '{}...'.format(m[:200])
        return m


class GitTagAdapter(GitObjectAdapter):
    columns = [('Name', 'name'),
               ('Message', 'message'),
               ('Date', 'date'),
               ('Commit', 'hexsha'),
               ('Commit Message', 'commit_message')]
    name_width = Int(60)
    commit_message_text = Property

    def _get_commit_message_text(self):
        return self._truncate_message(self.item.commit_message)


TAGS = 'TAG', 'BLANK', 'ISOEVO', 'ICFactor', 'COLLECTION, EDIT, MANUAL, IMPORT, SYNC'
TAG_COLORS = {'TAG': '#f5f7c8', 'BLANKS': '#cac8f7',
              'ISOEVO': '#c8f7e2', 'IMPORT': '#FAE8F0',
              'ICFactor': '#D2D4A7', 'COLLECTION': 'lightyellow'}


class CommitAdapter(GitObjectAdapter):
    columns = [('ID', 'hexsha'),
               ('Date', 'date'),
               ('Message', 'message'),
               ('Author', 'author'),
               ('Email', 'email'),
               ]
    author_width = Int(100)

    def get_bg_color(self, obj, trait, row, column=0):
        item = getattr(obj, trait)[row]
        color = TAG_COLORS.get(item.tag, 'white')

        return color


class TopologyAdapter(TabularAdapter):
    columns = [('Date', 'authdate'),
               ('Message', 'summary'),
               ('Author', 'author'),
               ('ID', 'oid')]
    oid_width = Int(80)


class CommitFactory(object):
    root_generation = 0
    commits = {}

    @classmethod
    def reset(cls):
        cls.commits.clear()
        cls.root_generation = 0

    @classmethod
    def new(cls, oid=None, log_entry=None):
        if not oid and log_entry:
            oid = log_entry[:40]
        try:
            commit = cls.commits[oid]
            if log_entry and not commit.parsed:
                commit.parse(log_entry)
            cls.root_generation = max(commit.generation,
                                      cls.root_generation)
        except KeyError:
            commit = Commit(oid, log_entry=log_entry)
            if not log_entry:
                cls.root_generation += 1
                commit.generation = max(commit.generation,
                                        cls.root_generation)
            cls.commits[oid] = commit
        return commit


class Commit(object):
    root_generation = 0

    __slots__ = ('oid',
                 'summary',
                 'parents',
                 'children',
                 'tags',
                 'author',
                 'authdate',
                 'email',
                 'generation',
                 'column',
                 'row',
                 'parsed')

    def __init__(self, oid=None, log_entry=None):
        super(Commit, self).__init__()

        self.oid = oid
        self.summary = ''
        self.parents = []
        self.children = []
        self.tags = set()
        self.email = None
        self.author = None
        self.authdate = None
        self.parsed = False
        self.generation = CommitFactory.root_generation
        self.column = None
        self.row = None
        if log_entry:
            self.parse(log_entry)

    def parse(self, log_entry, sep=logsep):

        oid, authdate, rauthdate, summary, author, email, tags, parents = log_entry.split(sep)

        self.oid = oid[:40]
        self.summary = summary if summary else ''
        self.author = author if author else ''
        self.authdate = authdate if authdate else ''
        self.email = email if email else ''

        if parents:
            generation = None
            for parent_oid in parents.split(' '):
                parent = CommitFactory.new(oid=parent_oid)
                parent.children.append(self)
                if generation is None:
                    generation = parent.generation + 1
                self.parents.append(parent)
                generation = max(parent.generation + 1, generation)
            self.generation = generation

        if tags:
            for tag in tags[2:-1].split(', '):
                self.add_label(tag)

        self.parsed = True
        return self

    def add_label(self, tag):
        """Add tag/branch labels from `git log --decorate ....`"""

        if tag.startswith('tag: '):
            tag = tag[5:]  # strip off "tag: " leaving refs/tags/

        if tag.startswith('refs/'):
            # strip off refs/ leaving just tags/XXX remotes/XXX heads/XXX
            tag = tag[5:]

        if tag.endswith('/HEAD'):
            return

        # Git 2.4 Release Notes (draft)
        # =============================
        #
        # Backward compatibility warning(s)
        # ---------------------------------
        #
        # This release has a few changes in the user-visible output from
        # Porcelain commands. These are not meant to be parsed by scripts, but
        # the users still may want to be aware of the changes:
        #
        # * Output from "git log --decorate" (and "%d" format specifier used in
        #   the userformat "--format=<string>" parameter "git log" family of
        #   command takes) used to list "HEAD" just like other tips of branch
        #   names, separated with a comma in between.  E.g.
        #
        #      $ git log --decorate -1 master
        #      commit bdb0f6788fa5e3cacc4315e9ff318a27b2676ff4 (HEAD, master)
        #      ...
        #
        # This release updates the output slightly when HEAD refers to the tip
        # of a branch whose name is also shown in the output.  The above is
        # shown as:
        #
        #      $ git log --decorate -1 master
        #      commit bdb0f6788fa5e3cacc4315e9ff318a27b2676ff4 (HEAD -> master)
        #      ...
        #
        # C.f. http://thread.gmane.org/gmane.linux.kernel/1931234

        head_arrow = 'HEAD -> '
        if tag.startswith(head_arrow):
            self.tags.add('HEAD')
            self.add_label(tag[len(head_arrow):])
        else:
            self.tags.add(tag)

    def is_fork(self):
        ''' Returns True if the node is a fork'''
        return len(self.children) > 1

    def is_merge(self):
        ''' Returns True if the node is a fork'''
        return len(self.parents) > 1
# ============= EOF =============================================
