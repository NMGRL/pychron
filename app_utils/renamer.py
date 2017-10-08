# ===============================================================================
# Copyright 2016 ross
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
import os
import shutil
from ConfigParser import ConfigParser
from datetime import datetime


def fcopytree(src, dest):
    def _copytree(name):
        s, d = os.path.join(src, name), os.path.join(dest, name)
        if os.path.isdir(s):
            print 'Copying {:<30s} to {}'.format(s, d)
            shutil.copytree(s, d)

    return _copytree


def welcome():
    print '''Welcome to Pychron Support Renamer
    '''


def run():
    root = os.path.expanduser('~')
    r = get_yes_no('Use home directory ({}) as root'.format(root))
    if not r:
        root = ''

    print 'Root directory: {}'.format(root)

    src = get_value('Source name', 'Source', default='PychronDev')

    src = os.path.join(root, src)
    dest = get_value('Destination name', 'Destination', default='Pychron')
    dest = os.path.join(root, dest)
    if os.path.isdir(dest):
        backup(dest)
        shutil.rmtree(dest)

    mode = get_value('Mode', 'Mode', default='rename')

    rename(src, dest, mode)


def rename(src, dest, mode):
    """

    :param src:
    :param dest:
    :param mode: rename or copy
    :return:
    """
    # edit the preferences file instead of copying
    if mode == 'rename':
        shutil.move(src, dest)
    elif mode == 'copy':
        shutil.copytree(src, dest)

    for app in ('pyexperiment', 'pyview'):
        ppath = os.path.join(dest, '.appdata', app, 'preferences.ini')
        if os.path.isfile(ppath):
            cfg = ConfigParser()
            cfg.read(ppath)

            cfg.set('pychron.general', 'environment', dest)

            with open(ppath, 'w') as wfile:
                cfg.write(wfile)
            break
    else:
        print 'Could not locate a preference file'


def backup(dest):
    root = os.path.dirname(dest)
    basename = os.path.basename(dest)
    dnow = datetime.now().strftime('%m-%d-%Y')
    basename = '{}{}'.format(basename, dnow)

    def func(i):
        d = os.path.join(root, '{}{:02n}'.format(basename, i))
        return d

    bname = os.path.join(root, basename)
    cnt = 1
    while 1:
        if not os.path.isdir(bname):
            break
        bname = func(cnt)
        cnt += 1

    r = get_yes_no('Use default backup name ({})'.format(bname))
    if not r:
        while 1:
            bname = get_value('Backup name', 'Backup name', default='PychronBackup')
            bname = os.path.join(root, bname)
            if not os.path.isdir(bname):
                break
            else:
                print '{} already exists'.format(bname)

    copytree = fcopytree(dest, bname)
    print 'Backup: {}'.format(bname)
    backup_log = get_yes_no('Backup logs', 'no')
    backup_data = get_yes_no('Backup data', 'no')
    if backup_log:
        copytree('logs')

    if backup_data:
        copytree('data')

    backup_all = get_yes_no('Backup all remaining')
    for d in ('.appdata', 'setupfiles', 'scripts',
              'queue_conditionals', 'experiments'):
        if backup_all or get_yes_no('Backup {}'.format(d)):
            copytree(d)


def get_value(msg, value, default=''):
    r = get_str(msg, default)
    print '{}: {}'.format(value, r)
    return r


def get_str(msg, default=''):
    str_default = ''
    if default:
        str_default = '[{}]'.format(default)

    r = raw_input('{} {}>> '.format(msg, str_default))
    if not r:
        r = default

    return r


def get_yes_no(msg, default='yes'):
    r = raw_input('{} [{}] >> '.format(msg, default))
    if not r:
        r = 'yes'

    return r.lower() in ('yes', 'y')


def main():
    welcome()
    run()


if __name__ == '__main__':
    main()
# ============= EOF =============================================
