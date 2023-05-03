# ===============================================================================
# Copyright 2011 Jake Ross
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

# =============enthought library imports=======================
# =============standard library imports ========================
from __future__ import absolute_import

import glob
import logging
import os
import shutil
from datetime import datetime
from logging.handlers import RotatingFileHandler

from pychron.core.helpers.filetools import list_directory, unique_path2
from pychron.paths import paths

NAME_WIDTH = 40
gFORMAT = (
    "%(name)-{}s: %(asctime)s %(levelname)-9s (%(threadName)-10s) %(message)s".format(
        NAME_WIDTH
    )
)
gLEVEL = logging.DEBUG


def simple_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter(gFORMAT))
    logger.addHandler(h)
    return logger


def get_log_text(n):
    root = logging.getLogger()
    for h in root.handlers:
        if isinstance(h, RotatingFileHandler):
            with open(h.baseFilename, "rb") as rfile:
                return tail(rfile, n)


def tail(f, lines=20):
    """
    http://stackoverflow.com/questions/136168/get-last-n-lines-of-a-file-with-python-similar-to-tail
    """
    total_lines_wanted = lines

    BLOCK_SIZE = 1024
    f.seek(0, 2)
    block_end_byte = f.tell()
    lines_to_go = total_lines_wanted
    block_number = -1
    blocks = []  # blocks of size BLOCK_SIZE, in reverse order starting
    # from the end of the file
    while lines_to_go > 0 and block_end_byte > 0:
        if block_end_byte - BLOCK_SIZE > 0:
            # read the last block we haven't yet read
            f.seek(block_number * BLOCK_SIZE, 2)
            blocks.append(f.read(BLOCK_SIZE))
        else:
            # file too small, start from begining
            f.seek(0, 0)
            # only read what was not read
            blocks.append(f.read(block_end_byte))
        lines_found = blocks[-1].count(b"\n")
        lines_to_go -= lines_found
        block_end_byte -= BLOCK_SIZE
        block_number -= 1
    all_read_text = b"".join(reversed(blocks))
    return b"\n".join(all_read_text.splitlines()[-total_lines_wanted:]).decode("utf-8")


# def anomaly_setup(name):
#     ld = logging.Logger.manager.loggerDict
#     print 'anomaly setup ld={}'.format(ld)
#     if name not in ld:
#         bdir = paths.log_dir
#         name = add_extension(name, '.anomaly')
#         apath, _cnt = unique_path2(bdir, name, delimiter='-', extension='.log')
#         logger = logging.getLogger('anomalizer')
#         h = logging.FileHandler(apath)
#         logger.addHandler(h)


def logging_setup(name, use_archiver=True, root=None, use_file=True, level=None, **kw):
    """ """
    # set up deprecation warnings
    # import warnings
    #     warnings.simplefilter('default')
    bdir = paths.log_dir if root is None else root

    # make sure we have a log directory
    # if not os.path.isdir(bdir):
    #     os.mkdir(bdir)
    #
    # if use_archiver:
    #     # archive logs older than 1 month
    #     # lazy load Archive because of circular dependency
    #     from pychron.core.helpers.archiver import Archiver
    #
    #     a = Archiver(archive_days=14, archive_months=1, root=bdir)
    #     a.clean()
    # if use_archiver:
    #     # archive logs older than 1 month
    #     # lazy load Archive because of circular dependency
    #     from pychron.core.helpers.archiver import Archiver
    #
    #     a = Archiver(archive_days=14,
    #                  archive_months=1,
    #                  root=bdir)
    #     a.clean(use_dirs=True)

    # if use_file:
    #     # create a new logging file
    #     logname = "{}.current.log".format(name)
    #     logpath = os.path.join(bdir, logname)
    #
    #     if os.path.isfile(logpath):
    #         backup_logpath, _cnt = unique_path2(
    #             bdir, name, delimiter="-", extension=".log", width=5
    #         )
    #         os.replace(logpath, backup_logpath)
    #         # shutil.copyfile(logpath, backup_logpath)
    #         # os.remove(logpath)
    #
    #         ps = list_directory(bdir, filtername=logname, remove_extension=False)
    #         for pi in ps:
    #             _h, t = os.path.splitext(pi)
    #             v = os.path.join(bdir, pi)
    #             os.replace(v, "{}{}".format(backup_logpath, t))
    #             # shutil.copyfile(v, "{}{}".format(backup_logpath, t))
    #             # os.remove(v)
    #         # move all log files there own directory
    #         # name directory based on logpath create date
    #         result = os.stat(logpath)
    #         mt = result.st_mtime
    #         creation_date = datetime.fromtimestamp(mt)
    #
    #         bk = os.path.join(bdir, creation_date.strftime('%y%m%d%H%M%S'))
    #         os.mkdir(bk)
    #         for src in glob.glob(os.path.join(bdir, '{}*'.format(logname))):
    #             shutil.move(src, bk)
    if use_file:
        # create a new logging file
        logname = "{}.current.log".format(name)
        logpath = os.path.join(bdir, logname)

        if os.path.isfile(logpath):
            # move all log files their own directory
            # name directory based on logpath create date
            result = os.stat(logpath)
            mt = result.st_mtime
            creation_date = datetime.fromtimestamp(mt)

            bk = os.path.join(bdir, creation_date.strftime("%y%m%d%H%M%S"))
            os.mkdir(bk)
            for src in glob.glob(os.path.join(bdir, "{}*".format(logname))):
                shutil.move(src, bk)

    root = logging.getLogger()
    if level is None:
        level = gLEVEL
    root.setLevel(level)
    shandler = logging.StreamHandler()

    handlers = [shandler]
    if use_file:
        rhandler = RotatingFileHandler(logpath, maxBytes=1e8, backupCount=50)
        handlers.append(rhandler)

    fmt = logging.Formatter(gFORMAT)
    for hi in handlers:
        hi.setLevel(gLEVEL)
        hi.setFormatter(fmt)
        root.addHandler(hi)


def add_root_handler(path, level=None, strformat=None, **kw):
    if level is None:
        level = gLEVEL

    if strformat is None:
        strformat = gFORMAT

    root = logging.getLogger()
    handler = logging.FileHandler(path, **kw)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(strformat))
    root.addHandler(handler)

    return handler


def remove_root_handler(handler):
    root = logging.getLogger()
    root.removeHandler(handler)


def new_logger(name):
    name = "{:<{}}".format(name, NAME_WIDTH)
    l = logging.getLogger(name)
    l.setLevel(gLEVEL)

    return l


def wrap(items, width=40, indent=90, delimiter=","):
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
            c = next(gcols)
            t += 1 + len(c)
            if t < width:
                r.append(c)
            else:
                rs.append(",".join(r))
                r = [c]
                t = len(c)

        except StopIteration:
            rs.append(",".join(r))
            break

    return ",\n{}".format(" " * indent).join(rs)


# ============================== EOF ===================================
