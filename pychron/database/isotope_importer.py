##===============================================================================
# # Copyright 2012 Jake Ross
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
##===============================================================================
#
##============= enthought library imports =======================
# from traits.api import HasTraits
# from traitsui.api import View, Item, TableEditor
# import os
# from pychron.database.adapters.isotope_adapter import IsotopeAdapter
# from pychron.paths import paths
##============= standard library imports ========================
##============= local library imports  ==========================
# def getter(header):
#    ind = lambda x:next((header.index(xi) for xi in [x.lower(), x.upper(), x.capitalize()]
#                         if xi in header
#                         ), None)
#    return lambda l, x:l[ind(x)]
#
# def import_file(path):
#
#
#    db = IsotopeAdapter(kind='sqlite',
#                      name=paths.isotope_db
#
#                      )
#    db.connect()
#    delim = '\t'
#    with open(path, 'r') as f:
#
#        header = f.next().strip().split(delim)
#
#        get = getter(header)
#
#        prev_l = 10000
#        for line in f:
#            if not line.strip():
#                continue
#            if line.startswith('#'):
#                continue
#            if line.startswith('----------'):
#                break
#
#            line = line.strip().split(delim)
#            if len(line) < len(header):
#                #assume its a missing labnumber
#                line.insert(0, None)
#
#            #add project
#            p = get(line, 'Project')
#            db.add_project(p)
#
#            #add user
#            u = get(line, 'User')
#            db.add_user(u, p)
#
#            #add material
#            m = get(line, 'Material')
#            db.add_material(m)
#
#            #add sample
#            s = get(line, 'sample')
#            db.add_sample(s, p, m)
#
#            #add labnumber
#            l = get(line, 'labnumber')
#
#            if l is None:
#                l = int(prev_l) + 1
#
#            prev_l = l
#            db.add_labnumber(l, s)
#
#            db.commit()
#
#
# if __name__ == '__main__':
#
# #    path = os.path.join(os.path.expanduser('~'), 'Sandbox', 'testdata')
#
#    import_file('testdata')
#
#
#
##============= EOF =============================================
