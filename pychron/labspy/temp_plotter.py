# ===============================================================================
# Copyright 2017 ross
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
import time

from matplotlib import pyplot as plt
from numpy import array, gradient

from pychron.labspy.database_adapter import LabspyDatabaseAdapter


def get_data():

    db = LabspyDatabaseAdapter(bind=False)
    db.host = os.getenv('Labspy_HOST')
    db.username = os.getenv('Labspy_USER')
    db.password = os.getenv('Labspy_PWD')
    db.name = os.getenv('Labspy_NAME')
    if db.connect():
        db.create_session()
        records = db.get_measurements('EnvironmentalMonitor', 'Lab Temp.', low='2017-06-14 12:00')
        xs, ys = zip(*[(r.pub_date, r.value) for r in records])
        return xs, ys


def plot(xs, ys):
    plt.subplot(211)
    plt.plot(xs, ys)
    plt.subplot(212)
    plt.plot(xs, gradient(array(ys)))
    plt.show()


def write(p, xs, ys):
    with open(p, 'w') as wfile:
        for xi, yi in zip(xs, ys):
            wfile.write('{},{},{}\n'.format(xi.strftime('%m/%d/%Y %H:%M:%S'), time.mktime(xi.timetuple()), yi))


xx,yy =get_data()
write('/Users/ross/Desktop/temp.csv', xx, yy)
# plot(xx,yy)

# ============= EOF =============================================
