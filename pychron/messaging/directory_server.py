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

#============= enthought library imports =======================
from traits.api import String, Str, Int
# from traitsui.api import View, Item, TableEditor
#============= standard library imports ========================
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from cStringIO import StringIO
import cgi
# import string, cgi, time
import os  # os. path
import urllib
import posixpath
import sys
import shutil
import mimetypes
from threading import Thread
#============= local library imports  ==========================
# ===============================================================================
# for debugging
# ===============================================================================
merc = os.path.join(os.path.expanduser('~'),
                        'Programming',
                        'mercurial')
src = os.path.join(merc, 'pychron_uv')
sys.path.insert(0, src)
# ===============================================================================
#
# ===============================================================================s

from pychron.loggable import Loggable

if not mimetypes.inited:
    mimetypes.init()  # try to read system mime.types

class DirectoryHandler(BaseHTTPRequestHandler):

    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream',  # Default
        '.py': 'text/plain',
        '.c': 'text/plain',
        '.h': 'text/plain',
        })

    def do_GET(self):
        f = self.send_head()
        if f:
            self._copy_file(f, self.wfile)
            f.close()

    def do_HEAD(self):
        f = self.send_head()
        if f:
            f.close()

    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.

        """

        path = self._translate_path(self.path)
        f = None
        if os.path.isdir(path):
            if not self.path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self._list_directory(path)
        ctype = self.guess_type(path)
        try:
            # Always read in binary mode. Opening files in text mode may cause
            # newline translations, making the actual size of the content
            # transmitted *less* than the content-length!
            f = open(path, 'rb')
        except IOError:
            self.send_error(404, "File not found")
            return None
        self.send_response(200)
        self.send_header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f

    def _copy_file(self, source, outputfile):
        shutil.copyfileobj(source, outputfile)

    def _list_directory(self, path):
        """Helper to produce a directory listing (absent index.html).

        Return value is either a file object, or None (indicating an
        error).  In either case, the headers are sent, making the
        interface the same as for send_head().

        """
        try:
            ll = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to ll directory")
            return None
        ll.sort(key=lambda a: a.lower())
        f = StringIO()
        displaypath = cgi.escape(urllib.unquote(self.path))
        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write("<html>\n<title>Directory listing for %s</title>\n" % displaypath)
        f.write("<body>\n<h2>Directory listing for %s</h2>\n" % displaypath)
        f.write("<hr>\n<ul>\n")
        for name in ll:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
                # Note: a link to a directory displays with @ and links with /
            f.write('<li><a href="%s">%s</a>\n'
                    % (urllib.quote(linkname), cgi.escape(displayname)))
        f.write("</ul>\n<hr>\n</body>\n</html>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        encoding = sys.getfilesystemencoding()
        self.send_header("Content-type", "text/html; charset=%s" % encoding)
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f

    def _translate_path(self, path):
        """Translate a /-separated PATH to the local filename syntax.

        Components that mean special things to the local file system
        (e.g. drive or directory names) are ignored.  (XXX They should
        probably be diagnosed.)

        """
        # abandon query parameters
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        path = posixpath.normpath(urllib.unquote(path))
        words = path.split('/')
        words = filter(None, words)

        path = self.server.root
#        path = os.getcwd()
        for word in words:
            _drive, word = os.path.splitdrive(word)
            _head, word = os.path.split(word)
            if word in (os.curdir, os.pardir): continue
            path = os.path.join(path, word)
        return path

    def guess_type(self, path):
        """Guess the type of a file.

        Argument is a PATH (a filename).

        Return value is a string of the form type/subtype,
        usable for a MIME Content-type header.

        The default implementation looks the file's extension
        up in the table self.extensions_map, using application/octet-stream
        as a default; however it would be permissible (if
        slow) to look inside the data to make a better guess.

        """

        _base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map['']

class _DirectoryServer(HTTPServer):
    root = ''

class DirectoryServer(Loggable):
    root = String
    host = Str
    port = Int
    _server = None

    def _root_changed(self):
        if self._server:
            self._server.root = self.root

    def start(self):
        t = Thread(target=self._start)
        t.start()
        return t

    def _start(self):
        self.info('Directory server started. {} {}'.format(self.host, self.port))
        self.info('serving {}'.format(self.root))

        host = self.host
        port = self.port
        if not host:
            host = 'localhost'
        if not port:
            port = 8080

        self._server = _DirectoryServer((host, port), DirectoryHandler)
        self._server.root = self.root
        self._server.serve_forever()

    def stop(self):
        self._server.shutdown()

def serve():
    try:
#        server = HTTPServer(('', 8080), MyHandler)
        server = DirectoryServer(host='localhost', port=8080)
        server.root = '/Users/ross/Sandbox/raster'
        print 'started httpserver...'
        server.start()

    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()

def main():
    serve()


if __name__ == '__main__':
    main()

# ============= EOF =============================================


