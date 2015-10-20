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
# ============= standard library imports ========================
import csv
from datetime import datetime, timedelta

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates




# ============= local library imports  ==========================
from pychron.database.isotope_database_manager import IsotopeDatabaseManager

"""
Plot a time series of peak centers
"""


def extract_data_csv(p):
    x, y = [], []
    with open(p, 'r') as rfile:
        reader = csv.reader(rfile)
        for row in reader:
            x.append(float(row[0]))
            y.append(float(row[1]))

    x, y = np.array(x), np.array(y)
    return x, y


def extract_data_db():
    x, y = [], []
    return x, y


def plot(x, y, o, ms):
    # n = -1
    # x = x[::-1]
    # y = y[::-1]

    # x -= x[-1]
    # x /= (24 * 3600.)
    # x *= -1
    x = np.array([datetime.fromtimestamp(xi) for xi in x])
    ay = np.ones(x.shape) * y.mean()

    yy = (y - ay)/ay * 100

    fig, ax = plt.subplots()
    ax.plot(x, yy, 'bo')

    # plt.xlabel('Days before 3/15')
    ax.set_ylabel('% Dev from Mean')
    ax.set_title('{} Peak Centers last 60 days'.format(ms.capitalize()))

    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))

    ax.xaxis.set_minor_locator(mdates.DayLocator(interval=5))
    ax.xaxis.set_minor_formatter(mdates.DateFormatter('%d'))

    fig.autofmt_xdate()

    plt.savefig(o)
    plt.show()

def plot2(x, y, x2,y2, o, ms, ms2):
    # n = -1
    # x = x[::-1]
    # y = y[::-1]

    x -= x[-1]
    x /= (24 * 3600.)

    x2 -= x2[-1]
    x2 /= (24 * 3600.)
    # x *= -1
    # x = np.array([datetime.fromtimestamp(xi) for xi in x])
    ay = np.ones(x.shape) * y.mean()
    ay2 = np.ones(x2.shape) * y2.mean()

    yy = (y - ay)/ay * 100
    yy2 = (y2 - ay2)/ay2 * 100

    fig, ax = plt.subplots()
    ax.plot(x, yy, 'bo', label=ms.capitalize())
    ax.plot(x2, yy2, 'ro', label=ms2.capitalize())

    # plt.xlabel('Days before 3/15')
    ax.set_ylabel('% Dev from Mean')
    ax.set_title('Peak Centers last 60 days'.format(ms.capitalize()))

    # ax.xaxis.set_major_locator(mdates.MonthLocator())
    # ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))

    # ax.xaxis.set_minor_locator(mdates.DayLocator(interval=5))
    # ax.xaxis.set_minor_formatter(mdates.DateFormatter('%d'))

    # fig.autofmt_xdate()
    plt.legend(loc='upper right')
    plt.savefig(o)
    plt.show()


def write_analyses_to_csv(p, ms):
    man = IsotopeDatabaseManager(bind=False, connect=False)
    man.db.trait_set(name='pychrondata',
                     kind='mysql',
                     host='129.138.12.160',
                     username='root',
                     password='DBArgon')

    man.connect()
    db = man.db

    with db.session_ctx():
        h = datetime.now()
        l = h - timedelta(days=60)
        ans = db.get_analyses_date_range(l, h, mass_spectrometers=ms)

        with open(p, 'w') as wfile:
            writer = csv.writer(wfile)
            n = len(ans)
            for i, ai in enumerate(ans):
                if not (i + 1) % 10:
                    print '{}/{}'.format(i + 1, n)
                try:
                    t = ai.timestamp
                    pc = ai.peak_center.center
                    # print ai.analysis_timestamp, t, pc
                    writer.writerow([t, pc])
                except AttributeError:
                    pass


def main():
    ms = 'obama'
    ms2 = 'jan'
    # ms = 'jan'

    p = '/Users/ross/Sandbox/peak_centers_{}.csv'.format(ms)
    p2 = '/Users/ross/Sandbox/peak_centers_{}.csv'.format(ms2)

    # o = '/Users/ross/Sandbox/peak_centers_{}.png'.format(ms)
    o = '/Users/ross/Sandbox/peak_centers_both.png'

    # write_analyses_to_csv(p, ms)

    x, y = extract_data_csv(p)
    x2, y2 = extract_data_csv(p2)
    # plot(x, y, o, ms)
    plot2(x[-30:], y[-30:], x2[-30:], y2[-30:], o, ms, ms2)


if __name__ == '__main__':
    main()

# ============= EOF =============================================