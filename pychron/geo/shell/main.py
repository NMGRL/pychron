#===============================================================================
# Copyright 2014 Jake Ross
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
from collections import namedtuple
import os

import pyproj

from pychron.core.helpers.iterfuncs import partition
from pychron.core.ui import set_qt


set_qt()
#============= enthought library imports =======================

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.paths import paths
from pychron.geo.shape_file_writer import ShapeFileWriter
from pychron.core.helpers.logger_setup import logging_setup
from pychron.geo.processor import GeoProcessor

paths.build('_dev')
logging_setup('geo')

Point = namedtuple('Point', 'x,y,sample,material,labnumber')

src = pyproj.Proj(init='EPSG:4326')
dest = pyproj.Proj(init='EPSG:3031')  #,proj='utm', zone='58')
# ellps='WGS84')

def proj_pt(lat, long):
    x, y = pyproj.transform(src, dest, long, lat)
    return x, y


def make_points(geo):
    db = geo.db
    pr = 'Minna Bluff'
    missing = []
    groups = []
    with db.session_ctx():
        v = db.get_project(pr)
        samples = v.samples
        yr1, yr2 = partition(samples, lambda x: x.name.startswith('MB06'))
        for name, sams in (('MB06_all_samples', yr1),
                           ('MB07_all_samples', yr2)):
            pts = []
            for s in sams:
                if not s.lat:
                    missing.append((s.name, s.alt_name))
                else:
                    print 'adding {} lat: {:0.5f} long: {:0.5f}'.format(s.name, s.lat, s.long)
                    x, y = proj_pt(s.lat, s.long)

                    pt = Point(x, y, s.name, s.material.name if s.material else '',
                               ','.join([li.identifier for li in s.labnumbers]))
                    pts.append(pt)
            groups.append((name, pts))
    return groups
    # print s.name, s.lat, s.long


def make_shape_file():
    geo = GeoProcessor(bind=False, connect=False)
    geo.db.trait_set(username='root', host='localhost',
                     kind='mysql',
                     password='Argon', name='pychrondata_dev')

    attrs = ['sample', 'material', 'labnumber']

    if geo.connect():
        groups = make_points(geo)

        writer = ShapeFileWriter()
        for name, pts in groups:
            # print name, pts
            p = os.path.join(paths.dissertation, 'data', 'minnabluff', 'gis', '{}.shp'.format(name))
            if writer.write_points(p, points=pts,
                                   attrs=attrs):
                pass


def main():
    make_shape_file()


if __name__ == '__main__':
    main()
#============= EOF =============================================
