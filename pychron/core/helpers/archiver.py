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
# ===============================================================================

# ============= enthought library imports =======================
from traits.api import Range, Bool, Str, HasTraits
# ============= standard library imports ========================
import os
import shutil
from datetime import datetime, timedelta
# ============= local library imports  ==========================
# from logger_setup import simple_logger
from pychron.core.helpers.logger_setup import simple_logger

MONTH_NAMES = ['JAN', 'FEB', 'MAR', 'APR', 'MAY',
               'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

# logger = logging.getLogger('Archiver')
# logger.setLevel(logging.DEBUG)
# h = logging.StreamHandler()
# h.setFormatter(logging.Formatter('%(name)-40s: %(asctime)s %(levelname)-7s (%(threadName)-10s) %(message)s'))
# logger.addHandler(h)

logger = simple_logger('Archiver')


class Archiver(HasTraits):
    archive_hours = Range(0, 23, 0)
    archive_days = Range(0, 31, 0)
    archive_months = Range(0, 12, 1)
    clean_archives = Bool(True)
    root = Str

    def info(self, msg, *args, **kw):
        logger.info(msg)

    def clean(self):
        self._clean()

    def _clean(self):
        """
            1. find all files older than archive_days+archive_hours
                - move to archive
            2. remove archive directories older than archive_months
        """
        root = self.root
        if not root:
            return

        archive_date = datetime.today() - timedelta(days=self.archive_days,
                                                    hours=self.archive_hours)
        self.info('Files older than {} will be archived'.format(archive_date))
        cnt = 0
        for p in self._get_files(root):
            rp = os.path.join(root, p)
            result = os.stat(rp)
            mt = result.st_mtime
            creation_date = datetime.fromtimestamp(mt)

            if creation_date < archive_date:
                self._archive(root, p)
                cnt += 1

        if cnt > 0:
            self.info('Archived {} files'.format(cnt))

        if self.clean_archives:
            self._clean_archive(root)
        self.info('Archive cleaning complete')

    def _get_files(self, root):
        return (p for p in os.listdir(root)
                if not p.startswith('.') and os.path.isfile(os.path.join(root, p)))

    def _clean_archive(self, root):
        self.info('Archives older than {} months will be deleted'.format(self.archive_months))
        arch = os.path.join(root, 'archive')
        rdate = datetime.today() - timedelta(days=self.archive_months * 30)

        if os.path.isdir(arch):
            for year_dir in self._get_files(arch):
                yarch = os.path.join(arch, year_dir)
                for month_dir in self._get_files(yarch):
                    adate = datetime(year=int(year_dir),
                                     month=MONTH_NAMES.index(month_dir) + 1,
                                     day=1)
                    if rdate > adate:
                        self.info('Deleting archive {}/{}'.format(year_dir,
                                                                  month_dir))
                        shutil.rmtree(os.path.join(arch, year_dir, month_dir))

                # remove empty year archives
                if not os.listdir(yarch):
                    self.info('Deleting empty year archive {}'.format(year_dir))
                    os.rmdir(yarch)

    def _archive(self, root, p):
        # create an archive directory
        today = datetime.today()
        month_idx = today.month
        month = MONTH_NAMES[month_idx - 1]
        year = today.year
        arch = os.path.join(root, 'archive')
        if not os.path.isdir(arch):
            os.mkdir(arch)

        yarch = os.path.join(arch, str(year))
        if not os.path.isdir(yarch):
            os.mkdir(yarch)

        mname = '{:02d}-{}'.format(month_idx, month)
        march = os.path.join(yarch, mname)
        if not os.path.isdir(march):
            os.mkdir(march)

        src = os.path.join(root, p)
        dst = os.path.join(march, p)

        self.info('Archiving {:30s} to ./archive/{}/{}'.format(p, year, mname))
        try:
            shutil.move(src, dst)
        except Exception, e:
            self.warning('Archiving failed')
            self.warning(e)


# if __name__ == '__main__':
# # from pychron.core.helpers.logger_setup import logging_setup, simple_logger, new_logger
#
#     logging_setup('video_main')
#     c = Archiver(archive_days=1
#     )
#     c.root = '/Users/ross/Sandbox/video_test'
#     c.clean()


