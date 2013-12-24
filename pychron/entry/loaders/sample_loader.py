#===============================================================================
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
#===============================================================================

#============= enthought library imports =======================
import pyproj

#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.loggable import Loggable
from pychron.core.xls.xls_parser import XLSParser


class SampleLoader(Loggable):
    """
        class to load sample info from a file and import into a database
        valid file formats: excel, csv
    """

    def do_import(self, manager, p):
        xp = XLSParser()
        xp.load(p, header_idx=2)
        overwrite_meta=True
        overwrite_alt_name=True
        db=manager.db
        progress=manager.open_progress(xp.nrows)

        with db.session_ctx():
            ellps= xp.get_value(0,1)
            zone= xp.get_value(1,1)

            convert_coordinates=xp.has_key('E') and xp.has_key('N')

            self._ref_system = pyproj.Proj(proj='utm', zone=zone, ellps=ellps.upper())
            self._wgs84 = pyproj.Proj(init='EPSG:4326')

            if convert_coordinates:
                keys=('sample','alt_name','project','material')
            else:
                keys=('sample','alt_name','project','material',
                      'lithology',
                      'lat','long','elevation','location','igsn','note')

            for args in xp.itervalues(keys=keys):
                sample, project, material=args['sample'], args['project'], args['material']

                progress.change_message('Setting sample {}'.format(sample))

                dbsample = db.get_sample(sample, project, material)
                # if not dbsample:
                #     self.info('adding sample {} project={} material={}'.format(sample, project, material))
                #     dbsample=db.add_sample(sample, project, material)
                if not dbsample:
                    dbsample=db.get_sample(args['alt_name'], project, material)
                    if dbsample:
                        if overwrite_alt_name:
                            dbsample.name=sample
                            dbsample.alt_name=args['alt_name']

                if not dbsample:
                    continue

                if overwrite_meta:
                    if convert_coordinates:
                        lon, lat= self._convert_coordinates(args['E'], args['N'])
                    else:
                        lat, lon=args['lat'], args['long']

                    dbsample.lat=lat
                    dbsample.long=lon
                    dbsample.elevation=args['elevation']
                    dbsample.location=args['location']
                    dbsample.igsn=args['igsn']
                    dbsample.note=args['note']
                    dbsample.lithology=args['lithology']

            progress.close()

    def _convert_coordinates(self, e, n):
        """
            convert E,N in coordinated system `ref` to lat, long
            use pyproj
        """

        return pyproj.transform(self._ref_system, self._wgs84, e, n)


#============= EOF =============================================

