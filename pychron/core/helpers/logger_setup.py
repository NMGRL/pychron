# ===============================================================================
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

#=============enthought library imports=======================

#=============standard library imports ========================
import os
import logging
#=============local library imports  =========================
from pychron.paths import paths
from filetools import unique_path2
import shutil

from pychron.core.helpers.filetools import list_directory
from logging.handlers import RotatingFileHandler

NAME_WIDTH = 40
gFORMAT = '%(name)-{}s: %(asctime)s %(levelname)-7s (%(threadName)-10s) %(message)s'.format(NAME_WIDTH)
gLEVEL = logging.DEBUG


def simple_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter(gFORMAT))
    logger.addHandler(h)
    return logger


def logging_setup(name, use_archiver=True, **kw):
    """
    """
    # set up deprecation warnings
    #     import warnings
    #     warnings.simplefilter('default')

    # make sure we have a log directory
    bdir = paths.log_dir
    if not os.path.isdir(bdir):
        os.mkdir(bdir)

    if use_archiver:
        # archive logs older than 1 month
        # lazy load Archive because of circular dependency
        from pychron.core.helpers.archiver import Archiver

        a = Archiver(archive_days=30,
                     archive_months=6,
                     root=bdir)
        a.clean()

    # create a new logging file
    logname = '{}.current.log'.format(name)
    logpath = os.path.join(bdir, logname)

    if os.path.isfile(logpath):
        backup_logpath, _cnt = unique_path2(bdir, name, extension='.log')

        shutil.copyfile(logpath, backup_logpath)
        os.remove(logpath)

        ps = list_directory(bdir, filtername=logname, remove_extension=False)
        for pi in ps:
            _h, t = os.path.splitext(pi)
            v = os.path.join(bdir, pi)
            shutil.copyfile(v, '{}{}'.format(backup_logpath, t))
            os.remove(v)

    root = logging.getLogger()
    root.setLevel(gLEVEL)
    shandler = logging.StreamHandler()
    rhandler = RotatingFileHandler(
        logpath, maxBytes=1e7, backupCount=5)
    for hi in (shandler, rhandler):
        hi.setLevel(gLEVEL)
        hi.setFormatter(logging.Formatter(gFORMAT))
        root.addHandler(hi)


def new_logger(name):
    name = '{:<{}}'.format(name, NAME_WIDTH)
    l = logging.getLogger(name)
    l.setLevel(gLEVEL)

    return l


def wrap(items, width=40, indent=90, delimiter=','):
    """
        wrap a list
    """
    if isinstance(items, str):
        items = items.split(delimiter)

    gcols = iter(items)
    t = 0
    rs = []
    r = []

    while 1:
        try:
            c = gcols.next()
            t += 1 + len(c)
            if t < width:
                r.append(c)
            else:
                rs.append(','.join(r))
                r = [c]
                t = len(c)

        except StopIteration:
            rs.append(','.join(r))
            break

    return ',\n{}'.format(' ' * indent).join(rs)

#============================== EOF ===================================