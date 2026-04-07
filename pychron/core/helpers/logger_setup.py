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
from typing import BinaryIO, Optional, Union, Tuple

from pychron.paths import paths

NAME_WIDTH = 40
gFORMAT = (
    "%(name)-{}s: %(asctime)s %(levelname)-9s (%(threadName)-10s) %(message)s".format(
        NAME_WIDTH
    )
)
gLEVEL = logging.DEBUG
PYCHRON_MANAGED_HANDLER = "_pychron_managed_handler"


def _coerce_level(level: Optional[Union[int, str]]) -> int:
    if level is None:
        return gLEVEL

    if isinstance(level, str):
        return getattr(logging, level.upper(), gLEVEL)

    return level


def _close_handler(handler: logging.Handler) -> None:
    handler.flush()
    handler.close()


def _clear_managed_root_handlers(root: logging.Logger) -> None:
    for handler in tuple(root.handlers):
        if getattr(handler, PYCHRON_MANAGED_HANDLER, False):
            root.removeHandler(handler)
            _close_handler(handler)


def simple_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(gLEVEL)

    for handler in logger.handlers:
        if getattr(handler, PYCHRON_MANAGED_HANDLER, False):
            break
    else:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(gFORMAT))
        setattr(handler, PYCHRON_MANAGED_HANDLER, True)
        logger.addHandler(handler)

    return logger


def get_log_text(n: int) -> Optional[str]:
    root = logging.getLogger()
    for h in root.handlers:
        if isinstance(h, RotatingFileHandler):
            with open(h.baseFilename, "rb") as rfile:
                return tail(rfile, n)
    return None


def tail(f: BinaryIO, lines: int = 20) -> str:
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


def _archive_old_logs(bdir: str, logname: str, use_archiver: bool = True) -> None:
    """Archive logs from previous session into timestamped directory."""
    logpath = os.path.join(bdir, logname)
    if not os.path.isfile(logpath):
        return

    # Create unique session directory based on file modification time
    result = os.stat(logpath)
    mt = result.st_mtime
    creation_date = datetime.fromtimestamp(mt)

    # Ensure uniqueness by appending counter if needed
    session_dir = os.path.join(bdir, creation_date.strftime("%y%m%d_%H%M%S"))
    counter = 1
    while os.path.exists(session_dir):
        session_dir = os.path.join(
            bdir, creation_date.strftime("%y%m%d_%H%M%S") + f"_{counter}"
        )
        counter += 1

    os.makedirs(session_dir, exist_ok=True)

    # Move all log files from this session
    for src in glob.glob(os.path.join(bdir, f"{logname}*")):
        shutil.move(src, session_dir)

    # Optionally archive old session directories
    if use_archiver:
        try:
            # Lazy load to avoid circular dependency
            from pychron.core.helpers.archiver import Archiver

            archiver = Archiver(archive_days=30, archive_months=3, root=bdir)
            archiver.clean(use_dirs=True)
        except ImportError:
            pass  # Archiver not available


def logging_setup(
    name: str,
    use_archiver: bool = True,
    root: Optional[str] = None,
    use_file: bool = True,
    **kw,
) -> None:
    """
    Set up logging for Pychron.

    Configures console and file handlers with rotation support.
    On startup, archives logs from previous session into a timestamped directory.

    Args:
        name: Logger name (e.g., 'pychron')
        use_archiver: If True, clean old archived sessions
        root: Override log directory (defaults to paths.log_dir)
        use_file: If True, create rotating file handler
        **kw: Additional keyword arguments
            - level: Log level (default: DEBUG)
    """
    bdir = paths.log_dir if root is None else root
    level = _coerce_level(kw.pop("level", None))

    if use_file:
        # Archive logs from previous session
        logname = f"{name}.current.log"
        _archive_old_logs(bdir, logname, use_archiver=use_archiver)
        logpath = os.path.join(bdir, logname)

    root = logging.getLogger()
    _clear_managed_root_handlers(root)
    root.setLevel(level)
    shandler = logging.StreamHandler()

    handlers = [shandler]
    if use_file:
        rhandler = RotatingFileHandler(logpath, maxBytes=1e8, backupCount=50)
        handlers.append(rhandler)

    fmt = logging.Formatter(gFORMAT)
    for hi in handlers:
        hi.setLevel(level)
        hi.setFormatter(fmt)
        setattr(hi, PYCHRON_MANAGED_HANDLER, True)
        root.addHandler(hi)


def add_root_handler(
    path: str,
    level: Optional[Union[int, str]] = None,
    strformat: Optional[str] = None,
    **kw,
) -> logging.Handler:
    if level is None:
        level = gLEVEL
    else:
        level = _coerce_level(level)

    if strformat is None:
        strformat = gFORMAT

    root = logging.getLogger()
    handler = logging.FileHandler(path, **kw)
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter(strformat))
    root.addHandler(handler)

    return handler


def remove_root_handler(handler: logging.Handler) -> None:
    root = logging.getLogger()
    root.removeHandler(handler)
    _close_handler(handler)


def new_logger(name: str) -> logging.Logger:
    name = "{:<{}}".format(name, NAME_WIDTH)
    l = logging.getLogger(name)
    l.setLevel(gLEVEL)

    return l


def check_log_disk_usage(
    log_dir: str, warn_threshold_gb: float = 2.0
) -> Tuple[float, bool]:
    """
    Check total disk usage of log directory.

    Args:
        log_dir: Path to log directory
        warn_threshold_gb: Threshold in GB to trigger warning (default: 2.0)

    Returns:
        Tuple of (total_size_gb, exceeded_threshold)
    """
    if not os.path.isdir(log_dir):
        return 0.0, False

    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(log_dir):
            for filename in filenames:
                try:
                    filepath = os.path.join(dirpath, filename)
                    total_size += os.path.getsize(filepath)
                except (OSError, IOError):
                    # File might have been deleted or permission denied
                    pass
    except (OSError, IOError):
        pass

    total_gb = total_size / (1024**3)
    exceeded = total_gb > warn_threshold_gb

    if exceeded:
        root_logger = logging.getLogger()
        if root_logger.handlers:
            root_logger.warning(
                f"Log directory {log_dir} is using {total_gb:.2f} GB "
                f"(exceeds {warn_threshold_gb:.1f} GB threshold)"
            )

    return total_gb, exceeded


def wrap(items, width: int = 40, indent: int = 90, delimiter: str = ",") -> str:
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
