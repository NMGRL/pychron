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



import time
import math
from datetime import datetime

ISO_FORMAT_STR = "%Y-%m-%d %H:%M:%S"


def time_generator(start=None):
    if start is None:
        start = time.time()
    while 1:
        yield time.time() - start


def current_time_generator(start):
    '''
    '''
    yt = start
    prev_time = 0
    i = 0
    while (1):

        current_time = time.time()
        if prev_time != 0:
            interval = current_time - prev_time
            yt += interval

        yield (yt)
        prev_time = current_time
        i += 1


def generate_datetimestamp(resolution='seconds'):
    '''
    '''
    ti = time.time()
    if resolution == 'seconds':
        r = time.strftime(ISO_FORMAT_STR)
    else:
        millisecs = math.modf(ti)[0] * 1000
        r = '{}{:0.5f}'.format(time.strftime(ISO_FORMAT_STR), millisecs)
    return r


def generate_datestamp():
    return get_date()


def get_datetime(timestamp=None):
    if timestamp is None:
        timestamp = time.time()

    if isinstance(timestamp, float):
        d = datetime.fromtimestamp(timestamp)
    else:
        d = datetime.strptime(timestamp, ISO_FORMAT_STR)
    return d


def get_date():
    return time.strftime('%Y-%m-%d')


def get_time(timestamp=None):
    if timestamp is None:
        timestamp = time.time()

    if isinstance(timestamp, float):
        timestamp = datetime.fromtimestamp(timestamp)

    t = time.mktime(timestamp.timetuple())
    return t


def convert_timestamp(timestamp, fmt=None):
    if fmt is None:
        fmt = ISO_FORMAT_STR
    t = get_datetime(timestamp)
    return datetime.strftime(t, fmt)

#    return time.mktime(t.timetuple()) + 1e-6 * t.microsecond
# def convert_float(timestamp):

def diff_timestamp(end, start=0):
    if not isinstance(end, datetime):
        end = datetime.fromtimestamp(end)
    if not isinstance(start, datetime):
        start = datetime.fromtimestamp(start)
    t = end - start
    h = t.seconds / 3600
    m = (t.seconds % 3600) / 60
    s = (t.seconds % 3600) % 60

    return t, h, m, s
