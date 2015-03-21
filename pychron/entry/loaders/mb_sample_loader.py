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
import pyproj
# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.core.xls.xls_parser import XLSParser


class SampleLoader(Loggable):
    """
        class to load sample info from a file and import into a database
        valid file formats: excel, csv
    """

    def _import_environment(self, manager, p):
        self._import_environment_sheet(manager, p, 'mb06', 'MB06')
        self._import_environment_sheet(manager, p, 'mb07', 'MB07')

    def _import_environment_sheet(self, manager, p, sheet, tag):
        xp = XLSParser()
        xp.load(p, sheet=sheet)
        db = manager.db

        with db.session_ctx():
            # progress = manager.open_progress(xp.nrows)
            for args in xp.itervalues():
                sample = args['sample']
                sample = '{}-{:03n}'.format(tag, int(sample))

                # progress.change_message('Setting environment for {}'.format(sample))
                dbsample = db.get_sample(sample, project='Minna Bluff', verbose=False)
                if dbsample:
                    mapf = args['MapFea'].lower()
                    env = None
                    if 'subaerial' in mapf:
                        env = 'subaerial'
                    elif 'hyaloclastite' in mapf:
                        env = 'subglacial'
                    elif 'quenched' in mapf:
                        env = 'mixed'

                    if env:
                        self.debug('setting sample: {} environment: {}'.format(sample, env))
                        dbsample.environment = env
                else:
                    self.debug('no sample in db for {}'.format(sample))

    def _import_tas(self, manager, p):
        xp = XLSParser()
        xp.load(p)
        db = manager.db

        with db.session_ctx():
            progress = manager.open_progress(xp.nrows)
            for args in xp.itervalues(keys=['sample', 'sio2', 'na2o', 'k2o']):
                sample = args['sample']

                progress.change_message('Setting sample {}'.format(sample))

                dbsample = db.get_sample(sample, project='Minna Bluff', verbose=False)
                if dbsample:
                    dbsample.sio2 = args['sio2']
                    dbsample.k2o = args['k2o']
                    dbsample.na2o = args['na2o']
                else:
                    print 'no sample in db for {}'.format(sample)
        progress.close()

    def _import_lithologies(self, manager, p):
        xp = XLSParser()
        xp.load(p)
        db = manager.db

        with db.session_ctx():
            progress = manager.open_progress(xp.nrows)
            for args in xp.itervalues(keys=['sample', 'lithology']):
                sample = args['sample']

                progress.change_message('Setting sample {}'.format(sample))

                dbsample = db.get_sample(sample, project='Minna Bluff', verbose=False)
                if dbsample:
                    dbsample.lithology = args['lithology']
                else:
                    print 'no sample in db for {}'.format(sample)
        progress.close()

    def _import_rock_type(self, manager, p):
        xp = XLSParser()
        xp.load(p)
        db = manager.db
        rock_type_map = {'L': 'Lava',
                         'LAg': 'Lava/Agglutinate',
                         'L(gl)': 'Lava glassy',
                         'B': 'Autobreccia',
                         'B(gl)': 'Hyaloclastite Breccia',
                         'D': 'Dike',
                         'VZI': 'Vent zone intrusion',
                         'T': 'Pyroclastic Tuff or Lapilli Tuff',
                         'S': 'Polymict sediment',
                         'T(gl)': 'Hydrovolcanic tuff  aka hyalotuff'}

        with db.session_ctx():
            progress = manager.open_progress(xp.nrows)
            for args in xp.itervalues(keys=['ID', 'MapCode']):
                sample = args['ID']
                sample = '{}-{}'.format(sample[:4], sample[4:])
                progress.change_message('Setting sample {}'.format(sample))

                dbsample = db.get_sample(sample, project='Minna Bluff', verbose=False)
                if dbsample:
                    # rock_type = rock_type_map[args['MapCode']]
                    rock_type = args['MapCode'].strip()
                    if rock_type in rock_type_map:
                        dbsample.rock_type = rock_type
                    else:
                        dbsample.rock_type = ''
                        # print sample, rock_type
                else:
                    print 'no sample in db for {}'.format(sample)
        progress.close()

    def do_import(self, manager, p):
        # self._import_lithologies(manager,p)
        # self._import_tas(manager, p)
        # self._import_environment(manager, p)
        self._import_rock_type(manager, p)
        return

        xp = XLSParser()
        xp.load(p, header_idx=2)
        overwrite_meta = True
        overwrite_alt_name = True
        add_samples = True
        db = manager.db
        progress = manager.open_progress(xp.nrows)

        self._import_lithologies(manager, db, xp)

        with db.session_ctx():
            ellps = xp.get_value(0, 1)
            zone = xp.get_value(1, 1)

            convert_coordinates = xp.has_key('E') and xp.has_key('N')

            self._ref_system = pyproj.Proj(proj='utm', zone=zone, ellps=ellps.upper())
            self._wgs84 = pyproj.Proj(init='EPSG:4326')

            if convert_coordinates:
                keys = ('sample', 'alt_name', 'project', 'material')
            else:
                keys = ('sample', 'alt_name', 'project', 'material',
                        'lithology',
                        'lat', 'long', 'elevation', 'location', 'igsn', 'note')

            for args in xp.itervalues(keys=keys):
                sample, project, material = args['sample'], args['project'], args['material']

                progress.change_message('Setting sample {}'.format(sample))

                dbsample = db.get_sample(sample, project, material, verbose=False)
                # if not dbsample:
                #     self.info('adding sample {} project={} material={}'.format(sample, project, material))
                #     dbsample=db.add_sample(sample, project, material)
                alt_name = args['alt_name']
                alt_names = None
                if alt_name:
                    head, tail = alt_name.split('-')
                    try:
                        itail = int(tail)
                        padded_alt_name = '{}-{:03n}'.format(head, itail)
                        non_padded_alt_name = '{}-{:01n}'.format(head, itail)
                    except ValueError:
                        padded_alt_name, non_padded_alt_name = '', ''

                    alt_names = (alt_name, padded_alt_name, non_padded_alt_name)

                if not dbsample:
                    if alt_names:
                        for a in alt_names:
                            dbsample = db.get_sample(a, project, material, verbose=False)
                            if dbsample:
                                if overwrite_alt_name:
                                    self.debug('setting name={} alt_name={}, padded_alt_name={}'.format(sample,
                                                                                                        a,
                                                                                                        padded_alt_name))
                                    dbsample.name = sample
                                    dbsample.alt_name = padded_alt_name
                                break

                if not dbsample:
                    if alt_names:
                        for a in alt_names:
                            dbsample = db.get_sample(a, project, material, verbose=False)
                            if dbsample:
                                break

                if not dbsample:
                    if add_samples:
                        if args['lat'] and args['long']:
                            dbsample = db.add_sample(sample, project, material)
                            if alt_name:
                                dbsample.alt_name = padded_alt_name

                if not dbsample:
                    continue

                if overwrite_meta:
                    if convert_coordinates:
                        lon, lat = self._convert_coordinates(args['E'], args['N'])
                    else:
                        lat, lon = args['lat'], args['long']

                    dbsample.lat = lat
                    dbsample.long = lon
                    dbsample.elevation = args['elevation']
                    dbsample.location = args['location']
                    dbsample.igsn = args['igsn']
                    dbsample.note = args['note']
                    dbsample.lithology = args['lithology']

            progress.close()

    def _convert_coordinates(self, e, n):
        """
            convert E,N in coordinated system `ref` to lat, long
            use pyproj
        """

        return pyproj.transform(self._ref_system, self._wgs84, e, n)


# ============= EOF =============================================

