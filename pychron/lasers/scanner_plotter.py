# ===============================================================================
# Copyright 2013 Jake Ross
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
# ============= standard library imports ========================
# ============= local library imports  ==========================
import os

from pylab import *


def plot_scan(p, name=None):
    data = genfromtxt(p, skip_header=2, delimiter=',', unpack=True)
    t, temp, power, rtemp, setpoint = data

    if name is None:
        name = os.path.basename(p)
    plot(t, power, label=name)
    xlabel('Time (s)')
    ylabel('Power (%)')
    legend()

def plot_rtemp(p, st=0, name=None):
    data = genfromtxt(p, skip_header=2, delimiter=',', unpack=True)
    t, temp, power, rtemp, setpoint = data

    if name is None:
        name = os.path.basename(p)
#    t += st

    # normalize
    rtemp -= rtemp[0]
    plot(t, rtemp, label=name)
    xlabel('Time (s)')
    ylabel('Delta-T (C)')

    legend(loc='upper left')

    return t[-1]

if __name__ == '__main__':
    root = '/Users/ross/Pychrondata/data/diode_reflector_scans/ordered'
#    root = '/Users/ross/Pychrondata/data/diode_reflector_scans/hole5'
#    root = '/Users/ross/Pychrondata/data/diode_reflector_scans/hole4'
    paths = os.listdir(root)
    st = 0
    for i, n in (
                (8, 'hole5 z=0  1100,1100'),
                (9, 'hole5 z=5  1000,1100'),
                (10, 'hole5 z=10  1000,1100'),
                (11, 'hole5 z=10  1000,1100'),
                (12, 'hole4 z=0  1000,1100'),
                (13, 'hole4 z=5  1000,1100'),
#                (16, 'hole5 z=0  1500,1600'),
#                (17, 'hole5 z=0  1500,1600'),
#                (15, 'hole5 z=5  1500,1600'),
#                (14, 'hole4 z=5  1500,1600'),
                # (8, 'hole4 z=5  1500,1600'),

                ):
        plot_rtemp(os.path.join(root, 'scan{:03n}.txt'.format(i)), name=n)
#
#    for po in paths:
#        if po.endswith('.txt'):
#            st = plot_rtemp(os.path.join(root, po),
#                            name=n)

#            plot_scan(os.path.join(root, po))
#    paths = (
#           ('scan008.txt', 'hole 5. z=0'),
#           ('scan009.txt', 'hole 5. z=5'),
#           ('scan012.txt', 'hole 4. z=0'),
#           ('scan013.txt', 'hole 4. z=5'),
#           )
#    for po, name in paths:
#
#        plot_scan(os.path.join(root, po), name=name)
#
#    xlim(0, 300)
#    xlabel('Time (s)')
#    ylabel('Power (%)')
    show()
# ============= EOF =============================================
