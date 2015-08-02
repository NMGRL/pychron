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
from git.exc import GitCommandError
from gitdb.util import hex_to_bin
from traits.api import HasTraits, Str, Bool, Date
# ============= standard library imports ========================
from datetime import datetime
import os
from git import Repo, Blob, Diff


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
    try:
        proc.wait()
    except GitCommandError:
        return []

    if not proc.returncode:
        return [from_gitlog(l.strip(), path, tag) for l in proc.stdout]


def get_diff(repo, a, b, path, change_type='M'):
    if isinstance(repo, (str, unicode)):
        if not os.path.isdir(repo):
            return
        repo = Repo(repo)

    # a = repo.commit(a)
    diff = repo.git.diff(a, b, '--full-index', '--', path)
    if diff:
        return fu(repo, diff)
        # ablob = Blob(repo, hex_to_bin(a_blob_id), mode=self.a_mode, path=a_path)
        # bblob = ''
        # return ablob, bblob


def fu(repo, text):
    for header in Diff.re_header.finditer(text):
        a_path, b_path, similarity_index, rename_from, rename_to, \
        old_mode, new_mode, new_file_mode, deleted_file_mode, \
        a_blob_id, b_blob_id, b_mode = header.groups()
        # new_file, deleted_file = bool(new_file_mode), bool(deleted_file_mode)

        # Our only means to find the actual text is to see what has not been matched by our regex,
        # and then retro-actively assin it to our index
        # if previous_header is not None:
        #     index[-1].diff = text[previous_header.end():header.start()]
        # end assign actual diff

        # Make sure the mode is set if the path is set. Otherwise the resulting blob is invalid
        # We just use the one mode we should have parsed
        a_mode = old_mode or deleted_file_mode or (a_path and (b_mode or new_mode or new_file_mode))
        b_mode = b_mode or new_mode or new_file_mode or (b_path and a_mode)
        ablob = Blob(repo, hex_to_bin(a_blob_id), mode=a_mode, path=a_path)
        bblob = Blob(repo, hex_to_bin(b_blob_id), mode=b_mode, path=a_path)
        return ablob, bblob

        # index.append(Diff(repo,
        #                   a_path and a_path.decode(defenc),
        #                   b_path and b_path.decode(defenc),
        #                   a_blob_id and a_blob_id.decode(defenc),
        #                   b_blob_id and b_blob_id.decode(defenc),
        #                   a_mode and a_mode.decode(defenc),
        #                   b_mode and b_mode.decode(defenc),
        #                   new_file, deleted_file,
        #                   rename_from and rename_from.decode(defenc),
        #                   rename_to and rename_to.decode(defenc),
        #                   None))
        #
        # previous_header = header

        # print 'diff', len(diff), diff

        # if change_type:
        #     # st = time.time()
        #     repo.git.diff(a,b,'--', '--names-only', path)
        #     # print 'gen time1 {}'.format(time.time()-st)
        #
        #     # direct git command is 10x faster than a.diff(b)
        #     st = time.time()
        #     gen = a.diff(b).iter_change_type(change_type)
        #     print 'gen time2 {}'.format(time.time()-st)
        # else:
        #     gen = a.diff(b)

        # rpath = os.path.relpath(path, repo.working_dir)

        # for d in gen:
        #     print d.a_blob.path, rpath
        #     if d.a_blob and d.a_blob.path == rpath:
        #         return d
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
