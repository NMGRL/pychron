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

#============= standard library imports ========================
import os


#============= local library imports  ==========================
from pychron.git_archive.repo_manager import GitRepoManager


class GitArchive(GitRepoManager):
    def __init__(self, root, *args, **kw):
        super(GitArchive, self).__init__(*args, **kw)
        # self.create_repo(root)
        self.open_repo(root)

    def close(self):
        del self._repo

    # def create_repo(self, p):
    #     if os.path.isdir(p):
    #         self._repo = Repo(p)
    #         return
    #
    #     os.mkdir(p)
    #     repo = Repo.init(p)
    #     self._repo = repo

    # def add(self, p, commit=True, message=None, message_prefix=None):
    #     repo = self._repo
    #     bp = os.path.basename(p)
    #     dest = os.path.join(repo.working_dir, bp)
    #     if message_prefix is None:
    #         message_prefix = 'modified' if os.path.isfile(dest) else 'added'
    #
    #     shutil.copyfile(p, dest)
    #
    #     index = repo.index
    #     index.add([dest])
    #     if commit:
    #         if message is None:
    #             message = '{}'.format(bp)
    #
    #         message = '{} - {}'.format(message_prefix, message)
    #         index.commit(message)

            # def get_history(self, p):
            #     return repo.git.log('--pretty=%H', '--follow', '--', p).split('\n')
            # return repo.git.log('--pretty=%H', '--follow', '--', p).split('\n')

    # def commits_iter(self, p, keys=None, limit='-'):
    #     repo = self._repo
    #     p = os.path.join(self._repo.working_tree_dir, p)
    #     print p
    #     hx = repo.git.log('--pretty=%H', '--follow', '-{}'.format(limit), p).split('\n')
    #
    #     def func(hi):
    #         commit = repo.rev_parse(hi)
    #         r = [hi, ]
    #         if keys:
    #             r.extend([getattr(commit, ki) for ki in keys])
    #         return r
    #
    #     return (func(ci) for ci in hx)

    # def unpack_blob(self, hexsha, p):
    #     repo = self._repo
    #     for bi in repo.rev_parse(hexsha).tree.blobs:
    #         if os.path.basename(bi.abspath) == p:
    #             return bi.data_stream.read()

    # def diff(self, a, b):
    #     repo = self._repo
    #     return repo.git.diff(a, b, )


# if __name__ == '__main__':
#     r = '/Users/ross/Sandbox/gitarchive'
#     g = GitArchive(r)
#
#     p = '/Users/ross/Sandbox/ga_test.txt'
#     for i in range(10):
#         with open(p, 'w') as fp:
#             fp.write('''iso,H2,H1,AX,L1,L2,CDD
# Ar40,{:0.5f},5.89559,6.00675,6.12358,6.24511,6.35683
# Ar39,5.89693,5.78828,5.89693,5.89693,5.89693,5.89693
# Ar36,5.56073,5.45620,5.56073,5.56073,5.56073,5.56073
# '''.format(i))
#
#         g.add(p)

#============= EOF =============================================

