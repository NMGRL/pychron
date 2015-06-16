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
from datetime import datetime
import os

from git import Repo
from traits.api import HasTraits, Str, Bool, Date



# ============= standard library imports ========================
# ============= local library imports  ==========================


class GitShaObject(HasTraits):
    message = Str
    date = Date
    blob = Str
    name = Str
    hexsha = Str
    author = Str
    email = Str
    active = Bool
    tag = Str

    # def traits_view(self):
    #     return View(UItem('blob',
    #                       style='custom',
    #                       editor=TextEditor(read_only=True)))
    #


def from_gitlog(obj, path, tag):
    hexsha, author, email, ct, message = obj.split('|')
    date = datetime.fromtimestamp(float(ct))
    g = GitShaObject(hexsha=hexsha,
                     message=message,
                     date=date,
                     author=author,
                     email=email,
                     path=path,
                     tag=tag)
    return g


def get_commits(repo, branch, path, tag, *args):
    if isinstance(repo, (str, unicode)):
        if not os.path.isdir(repo):
            return
        repo = Repo(repo)

    fmt = 'format:%H|%cn|%ce|%ct|%s'

    cmd = ['git', 'log', branch, '--pretty={}'.format(fmt)]
    cmd.extend(args)
    if path:
        cmd.extend(['--', path])
    proc = repo.git.execute(cmd, as_process=True)
    proc.wait()
    if not proc.returncode:
        return [from_gitlog(l.strip(), path, tag) for l in proc.stdout]


def get_diff(repo, a, b, path, change_type='M'):
    if isinstance(repo, (str, unicode)):
        if not os.path.isdir(repo):
            return
        repo = Repo(repo)

    a = repo.commit(a)
    if change_type:
        gen = a.diff(b).iter_change_type(change_type)
    else:
        gen = a.diff(b)

    rpath = os.path.relpath(path, repo.working_dir)

    for d in gen:
        if d.a_blob.path == rpath:
            return d
            # print 'sadf', d.a_blob.path

            # if d.
            # print d
            # print d.a_blob, d.b_blob

            # print '------------aa'
            # print d.a_blob.data_stream.read()
            # print '-----------bb'
            # if d.b_blob:
            # print d.b_blob.data_stream.read()

            # print repo.diff(a,b)
            # return []


if __name__ == '__main__':
    repo = '/Users/ross/Pychron_dev/data/.dvc/experiments/J-Curve'
    # for c in get_commits(repo, 'master', 'a-01/tag/-J-2562.tag.json', '--grep=^Update'):
    #     print c.hexsha, c.date, c.message
    # get_diff(repo, 'HEAD', '0ed461408fc8939909a907a73d2d991efc334eec')
    # get_diff(repo, '0ed461408fc8939909a907a73d2d991efc334eec', 'HEAD')
    get_diff(repo, 'HEAD~1', 'HEAD')

# ============= EOF =============================================
