# ===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Str, Int, Bool
# ============= standard library imports ========================
import httplib
import os
from cStringIO import StringIO
# ============= local library imports  ==========================
from pychron.loggable import Loggable
from apptools.preferences.preference_binding import bind_preference
from pychron.paths import paths
from pychron.core.xml.xml_parser import XMLParser
# from pychron.regex import make_image_regex

class MediaClient(Loggable):
    host = Str
    port = Int
    use_cache = Bool
    cache_dir = Str
    def url(self):
        return '{}:{}'.format(self.host, self.port)

    def __init__(self, *args, **kw):
        super(MediaClient, self).__init__(*args, **kw)
        self.bind_preferences()

# ===============================================================================
# filesystem
# ===============================================================================
    def _parse_propfind(self, resp):
        parser = XMLParser()

        parser.load(resp)
        tree = parser.get_tree()

        name = '{{DAV:}}{}'.format
        def get_response_name(elem):
            href = elem.find(name('href'))
            path = href.text.strip()
            return os.path.basename(path)

        return [get_response_name(ri) for ri in tree.findall(name('response'))]

    def ls(self, uri):
        resp = self.propfind(uri)
        return self._parse_propfind(resp)

    def bind_preferences(self):
        try:
            bind_preference(self, 'host', 'pychron.media_server.host')
            bind_preference(self, 'port', 'pychron.media_server.port')
            bind_preference(self, 'use_cache', 'pychron.media_server.use_cache')
            bind_preference(self, 'cache_dir', 'pychron.media_server.cache_dir')
        except AttributeError:
            pass


    def upload(self, path, dest=None):
        name = os.path.basename(path)
        if dest is not None:
            name = os.path.join(dest, name)

        with open(path, 'rb') as rfile:
            try:
                self._post(name, rfile.read())
                return True
            except Exception, e:
                print e

    def _new_connection(self):
        url = '{}:{}'.format(self.host, self.port)
        conn = httplib.HTTPConnection(url)
        return conn

    def propfind(self, uri):
        content = '''<?xml version='1.0' encoding='UTF-8'?>
<propfind xmlns="DAV:">
    <prop>
        <displayname/>
        <creationdate/>
        <getcontenttype/>
    </prop>
</propfind>
'''
        conn = self._new_connection()
        conn.putrequest('PROPFIND', '/{}'.format(uri))
        conn.putheader('DEPTH', 'infinity')
        conn.putheader('Content-type', 'text/xml')
        conn.putheader('Content-length', str(len(content)))
        conn.endheaders()
        conn.send(content)
        return conn.getresponse()

    def retrieve(self, name, output=None):

        '''
            return a file-like object
            !remember to close it!
        '''
        buf = None
        is_local = False
        if self.use_cache:
            buf = self._retrieve_local(name)
            if buf is not None:
                self.info('Using cached copy of {}'.format(name))
                is_local = True

        if buf is None:
            buf = self._retrieve_remote(name)

        if buf is None:
            self.info('No file named {}'.format(name))
        else:
            if output is not None:
                with open(output, 'wb') as wfile:
                    wfile.write(buf.read())

            if self.use_cache and not is_local:
                if not os.path.isdir(self.cache_dir):
                    nc = paths.default_cache
                    self.warning('Invalid cache directory {}. using default {}'.format(self.cache_dir, nc))
                    self.cache_dir = nc

                self.cache(name, buf)

            return buf

    def cache(self, path, buf=None):
        if buf is None:
            buf = open(path, 'r')

        if os.path.isdir(self.cache_dir):
            with open(os.path.join(self.cache_dir, os.path.basename(path)), 'w') as wfile:
                wfile.write(buf.read())
        else:
            self.warning('No cache directory available. {}'.format(self.cache_dir))

    def _retrieve_local(self, name):
        if not os.path.isdir(self.cache_dir):
            self.cache_dir = paths.default_cache

        path = os.path.join(self.cache_dir, os.path.basename(name))
        if os.path.isfile(path):
            return open(path, 'r')

    def _retrieve_remote(self, name):
        self.info('retrieve {} from remote directory'.format(name))
        resp = self._get(name)
        if resp is not None:
            buf = StringIO()
            buf.write(resp.read())
            buf.seek(0)
            return buf

    def _post(self, name, buf):
        conn = self._new_connection()
        conn.request('PUT', self._make_dest_path(name), buf)
        resp = conn.getresponse()
        if not (200 <= resp.status < 300):
            raise Exception(resp.read())

    def _get(self, name):
        conn = self._new_connection()
        conn.request('GET', self._make_dest_path(name))
        return conn.getresponse()

    def _make_dest_path(self, name):
        if not name.startswith('/'):
            name = '/{}'.format(name)
        return name

if __name__ == '__main__':

    c = MediaClient(host='localhost', port=8008)
    p = '/Users/ross/Sandbox/foo.png'
    p = '/Users/ross/Sandbox/figure_export.pdf'
#    print c.get_media('foo.txt', kind='txt')
#    print c.upload(p)
    c.retrieve('figure_export.pdf', 'mo3o.pdf')
# ============= EOF =============================================
