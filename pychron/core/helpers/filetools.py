#===============================================================================
# Copyright 2011 Jake Ross
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

#========== standard library imports ==========
import os
import subprocess


def view_file(p, application='Preview', logger=None):
    app_path = '/Applications/{}.app'.format(application)
    if not os.path.exists(app_path):
        app_path = '/Applications/Preview.app'

    try:
        subprocess.call(['open', '-a', app_path, p])
    except OSError:
        if logger:
            logger.debug('failed opening {} using {}'.format(p, app_path))
        subprocess.call(['open', p])


def list_directory(p, extension=None, filtername=None, remove_extension=False):
    ds = []
    #if extension:

    #return any([path.endswith(ext) for ext in extension.split(',')])
    #else:
    #    def test(path):
    #        return True

    if os.path.isdir(p):
        ds = os.listdir(p)
        if extension is not None:
            def test(path):
                for ext in extension.split(','):
                    if path.endswith(ext):
                        return True

            ds = [pi for pi in ds
                  if test(pi)]
        if filtername:
            ds = [pi for pi in ds if pi.startswith(filtername)]

    if remove_extension:
        ds = [os.path.splitext(pi)[0] for pi in ds]
    return ds


def add_extension(p, ext='.txt'):
    if not p.endswith(ext):
        # p += ext
        p = '{}{}'.format(p, ext)
    return p


def remove_extension(p):
    h, _ = os.path.splitext(p)
    return h


def unique_dir(root, base):
    p = os.path.join(root, '{}001'.format(base))
    i = 2
    while os.path.exists(p):
        p = os.path.join(root, '{}{:03n}'.format(base, i))
        i += 1

    os.mkdir(p)

    return p


def unique_path(root, base, extension='txt'):
    """

    """
    if extension:
        if '.' not in extension:
            extension = '.{}'.format(extension)
    else:
        extension = ''

    p = os.path.join(root, '{}-001{}'.format(base, extension))
    cnt = 1
    i = 2
    while os.path.isfile(p):
        p = os.path.join(root, '{}-{:03n}{}'.format(base, i, extension))
        i += 1
        cnt += 1

    return p, cnt


def to_bool(a):
    """
        a: a str or bool object

        if a is string
            'true', 't', 'yes', 'y', '1', 'ok' ==> True
            'false', 'f', 'no', 'n', '0' ==> False
    """

    if isinstance(a, bool):
        return a
    elif isinstance(a, (int, float)):
        return bool(a)

    tks = ['true', 't', 'yes', 'y', '1', 'ok']
    fks = ['false', 'f', 'no', 'n', '0']

    if a is not None:
        a = str(a).strip().lower()

    if a in tks:
        return True
    elif a in fks:
        return False


def parse_xy(p, delimiter=','):
    """
    """
    data = parse_file(p)
    if data:
        func = lambda i, data: [float(l.split(delimiter)[i]) for l in data]

        return func(0, data), func(1, data)


def commented_line(l):
    """
    """
    if l[:1] == '#':
        return True
    else:
        return False


def parse_file(p, delimiter=None, cast=None):
    """
        p: absolute path
        delimiter: str
        cast: callable. applied to each delimited field

    """
    if os.path.exists(p) and os.path.isfile(p):
        with open(p, 'U') as fp:
            r = filetolist(fp)
            if delimiter:
                if cast is None:
                    cast = str
                r = [map(cast, ri.split(delimiter)) for ri in r]

            return r


def parse_setupfile(p):
    """
    """

    fp = parse_file(p)
    if fp:
        return [line.split(',') for line in file]


def parse_canvasfile(p, kw):
    '''
    
    '''
    # kw=['origin','valvexy','valvewh','opencolor','closecolor']

    if os.path.exists(p) and os.path.isfile(p):
        with open(p, 'r') as fp:
            indices = {}
            i = 0
            f = filetolist(fp)
            count = 1
            for i in range(len(f)):
                if f[i][:1] == '!':
                    for k in kw:
                        if f[i][1:] == k:
                            i += 1
                            if k in indices:
                                k = k + str(count)
                                count += 1

                            indices[k] = f[i].split(',')

                            i += 1
                            break

            return indices


def filetolist(f, commentchar='#'):
    """
        f: file-like object
        return list
    """

    def isNewLine(c):
        return c == chr(10) or c == chr(13)

    def test(li):
        cc = li[:1]
        return not (cc == commentchar or isNewLine(cc))

    r = (line for line in f if test(line))
    r = [line.split(commentchar)[0].strip() for line in r]
    # r = []
    #
    # for line in f:
    #     cc = line[:1]
    #     if not cc == commentchar and not isNewLine(cc):
    #         # l = line[:-1] if line[-1:] == '\n' else line
    #         # remove inline comments
    #         line = line.split('#')[0]
    #         r.append(line.strip())
    return r


def fileiter(fp, commentchar='#', strip=False):
    def isNewLine(c):
        return c in ('\r', '\n')

    def test(li):
        cc = li[:1]
        return not (cc == commentchar or isNewLine(cc))

    for line in fp:
        if test(line):
            if strip:
                line = line.strip()
            yield line

