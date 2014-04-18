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
import csv
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

SamplePoint = namedtuple('SamplePoint', 'x,y,sample,material,labnumber')

src = pyproj.Proj(init='EPSG:4326')
dest = pyproj.Proj(init='EPSG:3031')  #,proj='utm', zone='58')
# ellps='WGS84')

def proj_pt(lat, long):
    x, y = pyproj.transform(src, dest, long, lat)
    return x, y


def get_processor(database='pychrondata_dev'):
    geo = GeoProcessor(bind=False, connect=False)
    geo.db.trait_set(username='root', host='localhost',
                     kind='mysql',
                     password='Argon', name=database)
    return geo


def make_sample_points(geo):
    db = geo.db
    pr = 'Minna Bluff'
    missing = []
    groups = []
    with db.session_ctx():
        v = db.get_project(pr)
        samples = v.samples
        yr1, yr2 = partition(samples, lambda x: x.name.startswith('MB06'))
        for name, sams in (('MB06_all_samples', yr1),):
            #('MB07_all_samples', yr2)):
            pts = []
            for s in sams:
                if not s.lat:
                    missing.append((s.name, s.alt_name))
                else:
                    print 'adding {} lat: {:0.5f} long: {:0.5f}'.format(s.name, s.lat, s.long)
                    x, y = proj_pt(s.lat, s.long)

                    pt = SamplePoint(x, y, s.name, s.material.name if s.material else '',
                                     ','.join([li.identifier for li in s.labnumbers]))
                    pts.append(pt)
            groups.append((name, pts))
    return groups
    # print s.name, s.lat, s.long


def make_sample_shape_file(dbname):
    geo = get_processor(dbname)
    attrs = ['sample', 'material', 'labnumber']
    atypes = ['C', 'C', 'C']
    attrs = zip(attrs, atypes)

    if geo.connect():
        groups = make_sample_points(geo)

        writer = ShapeFileWriter()
        for name, pts in groups:
            # print name, pts
            p = os.path.join(paths.dissertation, 'data', 'minnabluff', 'gis', '{}.shp'.format(name))
            if writer.write_points(p, points=pts,
                                   attrs=attrs):
                pass


def make_interpreted_age_points(geo):
    # iag = 'AllAges2'
    iag_id = 29
    attrs = ['sample', 'material', 'labnumber', 'age', 'age_err', 'age_kind', 'elevation']
    atypes = ['C', 'C', 'C', 'N', 'N', 'C', 'N']

    AgePoint = namedtuple('SamplePoint', ','.join(['x', 'y'] + attrs))

    db = geo.db
    pts = []
    missing = []
    with db.session_ctx():
        hist = db.get_interpreted_age_group_history(iag_id)
        print len(hist.interpreted_ages)

        for ia in hist.interpreted_ages:
            aa = ia.history.interpreted_age
            ln = ia.history.identifier
            ln = db.get_labnumber(ln)
            s = ln.sample
            if not s.lat:
                missing.append((s.name, s.alt_name))
            else:
                print 'adding {} lat: {:0.5f} long: {:0.5f}'.format(s.name, s.lat, s.long)
                x, y = proj_pt(s.lat, s.long)
                print s.elevation
                pts.append(AgePoint(x, y,
                                    s.name,
                                    s.material.name if s.material else '',
                                    ln.identifier,
                                    aa.age, aa.age_err, aa.age_kind, s.elevation))

    return pts, zip(attrs, atypes)


def make_binned_elevations(dbname):
    geo = get_processor(dbname)
    if geo.connect():
        pts, attrs = make_interpreted_age_points(geo)
        root = os.path.join(paths.dissertation, 'data', 'minnabluff', 'gis')
        root = os.path.join(root, 'construct_evo')
        pts = sorted(pts, key=lambda x: x.age)
        ps = [pts[0].elevation]
        cbin = int(pts[0].age)
        p = os.path.join(root, 'elevations.txt')

        def write_row(cbin, pp):
            mi, ma = min(pp), max(pp)
            writer.writerow((cbin, mi, ma, ma - mi ))

        with open(p, 'w') as fp:
            writer = csv.writer(fp)

            for po in pts[1:]:
                if int(po.age) != cbin:
                    write_row(cbin, ps)
                    # writer.writerow((cbin,mi, ma, ma-mi ))
                    ps = [po.elevation]
                    cbin = int(po.age)
                else:
                    ps.append(po.elevation)

            if ps:
                write_row(cbin, ps)


def make_interpreted_age_shape_file(dbname, group=False):
    name = 'interpreted_ages'

    geo = get_processor(dbname)
    if geo.connect():
        pts, attrs = make_interpreted_age_points(geo)

        root = os.path.join(paths.dissertation, 'data', 'minnabluff', 'gis')

        if group:
            root = os.path.join(root, 'construct_evo')
            pts = sorted(pts, key=lambda x: x.age)
            ps = pts[:1]
            cbin = int(ps[0].age)
            for po in pts[1:]:
                if int(po.age) != cbin:
                    p = os.path.join(root, 'ages_{:02n}'.format(cbin))
                    write_shape_file(ps, attrs, p)
                    ps = [po]
                    cbin = int(po.age)
                else:
                    ps.append(po)

            if ps:
                p = os.path.join(root, 'ages_{:02n}'.format(cbin))
                write_shape_file(ps, attrs, p)

        else:
            p = os.path.join(root, '{}.shp'.format(name))
            write_shape_file(pts, attrs, p)
            #write to csv
            p = os.path.join(root, '{}.csv'.format(name))
            with open(p, 'w') as fp:
                writer = csv.writer(fp)
                writer.writerow(attrs)
                for pt in pts:
                    data = [getattr(pt, ai[0]) for ai in attrs]
                    writer.writerow(data)


def write_shape_file(pts, attrs, p):
    writer = ShapeFileWriter()
    writer.write_points(p, points=pts,
                        attrs=attrs)


def main():
    # make_sample_shape_file('pychrondata_minnabluff')
    make_interpreted_age_shape_file('pychrondata_minnabluff')
    # make_binned_elevations('pychrondata_minnabluff')


if __name__ == '__main__':
    main()
#============= EOF =============================================
