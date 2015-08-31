## ===============================================================================
# # Copyright 2011 Jake Ross
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #   http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
## ===============================================================================
#
#
#
# import csv
# from pychron.database.pychron_adapter import PychronAdapter
# from tables import open_file
# import os
# from pychron.managers.data_managers.h5_data_manager import H5DataManager
# import time
# from datetime import time as dtime
#
# FITS = dict(L=1, P=2, A=3)
#
# class Loader(object):
#
#    def import_autoupdate(self, p):
#        ad = self.adapter
#        dm = self.data_manager
#
#        dpath = ad.get_analyses_path()
#        with open(p, 'U') as f:
#            reader = csv.reader(f, delimiter='\t')
#            header = reader.next()
#
#            for l in reader:
#                #the rest is metadata
#                if l[0] == '':
#                    break
#
#                #add an analysis to the analyses table
#                aid = 1
#                runtime = l[header.index('Run_Hour')]
#                runtime = float(runtime)
#
#                rt = dtime(hour=int(runtime), minute=int(runtime % 1 * 60))
#                rundate = l[header.index('Run_Date')]
#                #convert rundate
#                d = time.strptime(rundate, '%m/%d/%y')
#                rundate = time.strftime('%Y-%m-%d', d)
#
#                aid = ad.add_analysis(rundate=rundate,
#                                      runtime=rt,
#                                      atype='air',
#                                      spectype='obama',
#                                      )
#
#                #add to intercepts table
#                d = dict(analysis_id=aid)
#
#                ft = l[header.index('Fit_Type')]
#
#                for k, e, j in [('Ar{}_'.format(i), 'Ar{}_Er'.format(i), i) for i in range(36, 41)]:
#                    ind = header.index(k)
#                    eind = header.index(e)
#                    m = 0
#                    er = 0
#                    try:
#                        m = float(l[ind])
#                        er = float(l[eind])
#                    except ValueError:
#                        pass
#                    d['m{}'.format(j)] = m
#                    d['m{}er'.format(j)] = er
#                    d['fit{}'.format(j)] = FITS[ft[40 - j]]
#
#                ad.add_intercepts(**d)
#
#
# if __name__ == '__main__':
#
#    adapter = PychronAdapter()
#    adapter.connect()
#
#    dm = H5DataManager()
#
#    l = Loader()
#    l.adapter = adapter
#    l.data_manager = dm
#
#    p = '/Users/ross/Desktop/deadtime_full'
#    l.import_autoupdate(p)
#
#    print adapter.get_intercepts(analysis_id=1)
##======== EOF ================================
