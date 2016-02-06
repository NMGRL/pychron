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
import os
import random
import subprocess

import matplotlib.pyplot as plt

from pychron.core.ui import set_qt

set_qt()

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.dvc.dvc import DVC

"""
proof of concept test see gist https://gist.github.com/jirhiker/3ba3e1e358ef933fa9b5


"""
dvc = DVC(clear_db=True, auto_add=True)
DP = dvc.db.path

units_map = {'K': 1e3, 'M': 1e6, 'G': 1e9}


def get_dir_size(path):
    return subprocess.check_output(['du', '-sh', path]).split()[0].decode('utf-8')


def report_irrad_stats(wfile, nirrads, nlevels, npositions):
    if nirrads == 1 and nlevels == 1:
        print '{:<10s}{:<10s}{:<10s}{:<10s}{:<10s}'.format('irrad', 'level', 'pos', 'sizedb', 'sizegit')
        wfile.write('{}\n'.format(','.join(('irrad', 'level', 'pos', 'sizedb', 'sizegit'))))

    size = os.path.getsize(DP)
    size2 = get_dir_size(os.path.join(dvc.meta_repo.path, '.git'))

    print '{:<10}{:<10d}{:<10d}{:<10s}{:<10s}'.format(nirrads, nlevels, npositions, '{}K'.format(int(size / 1000.)),
                                                      size2)

    units = size2[-1]
    size2 = float(size2[:-1]) * units_map[units]
    wfile.write('{},{},{},{},{}\n'.format(nirrads, nlevels, npositions,
                                          size, size2))


def add_project(p):
    with dvc.db.session_ctx():
        dvc.db.add_project(p)


def add_sample(s, p, m):
    with dvc.db.session_ctx():
        dvc.db.add_sample(s, p, m)


def add_position(irrad, level, pos):
    with dvc.db.session_ctx():
        dvc.db.add_irradiation_position(irrad, level, pos)


def add_irradiation(irrad):
    with dvc.db.session_ctx():
        dvc.db.add_irradiation(irrad)


def add_level(irrad, level, holder):
    with dvc.db.session_ctx():
        dvc.db.add_irradiation_level(irrad, level, holder)


def add_material(mat):
    with dvc.db.session_ctx():
        dvc.db.add_material(mat)


def do(wfile):
    pcount = 0
    scount = 0
    nirrads = 5
    nlevels = 20
    npositions = 40

    materials = ['san', 'ban', 'gmc', 'horn', 'feld', 'musc', 'plag', 'alb', 'crypt', 'jar', 'alu']
    for mat in materials:
        add_material(mat)

    for i in range(nirrads):
        irrad = 'NM-{:03d}'.format(i)
        add_irradiation(irrad)
        for l in range(nlevels):
            level = chr(65 + l)
            add_level(irrad, level, '{}Holes.txt'.format(npositions))
            ps = []
            for p in (0, 1):
                name = 'Project{:03d}'.format(pcount)
                name = '{}.{:032X}'.format(name, hash(name))
                add_project(name)
                pcount += 1
                ps.append(name)

            for pp in range(npositions):
                if pp >= npositions / 2:
                    project = ps[1]
                else:
                    project = ps[0]

                sample = '{:04d}.{:032X}'.format(scount, hash('{}{}'.format(project, scount)))
                add_sample(sample, project, random.choice(materials))
                scount += 1
                add_position(irrad, level, pp)

            dvc.commit_db()
            report_irrad_stats(wfile, i + 1, i * nlevels + l + 1, (i * nlevels * npositions) + l * npositions + pp + 1)

            # for i in range(100):
            # add_analysis()
            # report_stats()


def plot_results():
    with open('results.txt', 'r') as rfile:
        xs = []
        dbs = []
        gits = []
        rfile.next()
        for i, line in enumerate(rfile):
            xs.append(i)

            args = line.split(',')
            s = float(args[-2])
            s2 = float(args[-1])
            dbs.append(s)
            gits.append(s2)

        plt.plot(xs, dbs)
        plt.plot(xs, gits)
        plt.show()


def main():
    with open('results.txt', 'w') as wfile:
        do(wfile)

        # plot_results()


if __name__ == '__main__':
    main()
# ============= EOF =============================================



