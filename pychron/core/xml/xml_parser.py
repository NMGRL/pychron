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
# from xml.etree.ElementTree import ElementTree, Element, ParseError
import os

from lxml import etree
from lxml.etree import ElementTree, Element, ParseError, XML
from pyface.message_dialog import warning

#============= local library imports  ==========================


def extract_xml_text(txt):
    """
        return an xml root object
    """
    elem = XML(txt)
    ntxt = elem.text
    if ntxt is None:
        ntxt = ''
        for ei in elem.iter():
            if ei.text is not None:
                ntxt += ei.text

    return ntxt


class XMLParser(object):
    _root = None

    def __init__(self, path=None, *args, **kw):
        if path:
            self._path = path
            try:
                self._parse_file(path)
            except ParseError, e:
                warning(None, str(e))
        else:
            self._root = Element('root')

    def _parse_file(self, p):
        path = None
        if isinstance(p, (str, unicode)):
            if os.path.isfile(p):
                if isinstance(p, str):
                    path = open(p, 'r')

        if path:
            txt = path.read()
            self._root = XML(txt)
            path.close()
            return True

    def load(self, fp):
        return self._parse_file(fp)

    def add(self, tag, value, root, **kw):
        if root is None:
            root = self._root
        elem = self.new_element(tag, value, **kw)
        root.append(elem)
        return elem

    def new_element(self, tag, value, **kw):
        e = Element(tag, attrib=kw)
        if value not in ('', None):
            e.text = str(value)
        return e

    def get_root(self):
        return self._root

    def get_tree(self):
        return ElementTree(self._root)

    def save(self, p=None, pretty_print=True):
        if p is None:
            p = self._path

        if p and os.path.isdir(os.path.dirname(p)):
            tree = self.get_tree()
            tree.write(p,
                       xml_declaration=True,
                       method='xml',
                       pretty_print=pretty_print)

    def tostring(self, pretty_print=True):
        tree = self.get_tree()
        if tree:
            return etree.tostring(tree, pretty_print=pretty_print)

    def get_elements(self, name=None):
        root = self.get_root()
        path = '//{}'.format(name)
        return root.xpath(path)

    #         return self._get_elements(None, True, name)

    def _get_elements(self, group, element, name):
        if group is None:
            group = self.get_root()
        return [v if element else v.text.strip()
                for v in group.findall(name)]


class XMLParser2(object):
    '''
        wrapper for ElementTree
    '''
    _tree = None

    def __init__(self, path=None, *args, **kw):
        self._tree = ElementTree()
        if path:
            self._path = path
            try:
                self._parse_file(path)
            except ParseError, e:
                warning(None, str(e))

    def load(self, fp):
        '''
            path or file-like object
        '''
        return self._parse_file(fp)

    def _parse_file(self, p):
        self._tree.parse(p)

    def get_tree(self):
        return self._tree

    def save(self, p=None):
        if p is None:
            p = self._path

        if p and os.path.isdir(os.path.dirname(p)):
        #        self.indent(self._tree.getroot())
            self._tree.write(p, pretty_print=True)

            #    def indent(self, elem, level=0):
            #        i = '\n' + level * '  '
            #        if len(elem):
            #            if not elem.text or not elem.text.strip():
            #                elem.text = i + '  '
            #            if not elem.tail or not elem.tail.strip():
            #                elem.tail = i
            #            for elem in elem:
            #                self.indent(elem, level + 1)
            #            if not elem.tail or not elem.tail.strip():
            #                elem.tail = i
            #        else:
            #            if level and (not elem.tail or not elem.tail.strip()):
            #                elem.tail = i

    def add_element(self, tag, value, root, **kw):
        if root is None:
            root = self._tree.getroot()
        elem = self.new_element(tag, value, **kw)
        root.append(elem)
        return elem

    def new_element(self, tag, value, **kw):
        e = Element(tag, attrib=kw)
        #        if value:
        #            e.text = value
        return e

        #============= EOF ====================================
