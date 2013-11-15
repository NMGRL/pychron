#===============================================================================
# Copyright 2011 Jake Ross
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

#============= standard library imports ========================

#============= local library imports  ==========================
from xml_parser import XMLParser
class HWCParser(XMLParser):
    def get_class_attributes(self):
        r = []
        c = self._tree.find('class')
        for a in c.iter('attr'):
            name = a.get('name')
            attr = a.text
            r.append((name, attr))
        return r

    def get_functions(self):
        r = []
        for f in self._tree.iter('func'):
            name = f.find('name').text
            body = 'pass'
            args = 'a'
            args = ', '.join([a.text for a in f.findall('arg')])

            body = '''cmd='{command}'
        resp=self.ask(self._build_command(cmd))
        return self._parse_response(resp)
'''.format(command=f.find('command').text)


            kwargs = ', '
            for kw in f.findall('kwarg'):
                kwargs += '{}={}'.format(kw.get('name'),
                                       kw.text)
            if kwargs == ', ':
                kwargs = ''

            d = dict(name=name,
                   args=args,
                   kwargs=kwargs,
                   body=body
                   )
            r.append(d)

        return r
#============= EOF ====================================
