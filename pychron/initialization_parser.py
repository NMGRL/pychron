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
from lxml.etree import Element
from pyface.message_dialog import warning
#============= standard library imports ========================
import os
import sys
import inspect
#============= local library imports  ==========================
from pychron.core.helpers.filetools import to_bool
from pychron.core.xml.xml_parser import XMLParser
from pychron.paths import paths

lower = lambda x: x.lower() if x else None


def handle_uncaught_exception(func):
    def _handle(*args, **kw):
        try:
            return func(*args, **kw)
        except Exception, e:
            import traceback

            traceback.print_exc()
            warning(None, 'There is a problem in your initialization file {}'.format(e))
            sys.exit()

    return _handle


def decorate_all(cls):
    """
         adds the handle_uncaught_exception decorator to all methods of the class
    """

    for name, m in inspect.getmembers(cls, inspect.ismethod):
        setattr(cls, name, handle_uncaught_exception(m))
    return cls


@decorate_all
class InitializationParser(XMLParser):
    """
    """
    def __init__(self, *args, **kw):
        ver = '_proc'
        # ver = '_exp'
        #ver = '_exp_uv'
        #ver= '_spec'
        # ver='_diode'
        # ver = '_dash'
        #ver = '_dash_client'
        #ver = ''
        p = os.path.join(paths.setup_dir, 'initialization{}.xml'.format(ver))
        if not os.path.isfile(p):
            p = os.path.join(paths.setup_dir, 'initialization.xml')
            if not os.path.isfile(p):
                warning(None, 'No initialization file.\n{} is not a valid file'.format(p))
                sys.exit()

        super(InitializationParser, self).__init__(p, *args, **kw)

    def add_plugin(self, category, name):
        tree = self.get_root()
        cat = tree.find(category)
        cat.append(self.new_element('plugin', name, enabled='false'))
        self.save()

    def get_plugins(self, category=None, all_=False, element=False):
        tree = self.get_root()
        tree = tree.find('plugins')
        if category:
            cat = tree.find(category)
            if cat is not None:
                plugins = cat.findall('plugin')
        else:
            try:
                plugins = tree.iter(tag='plugin')
            except AttributeError:
                plugins = tree.getiterator(tag='plugin')

        return [p if element else p.text.strip()
                for p in plugins if all_ or to_bool(p.get('enabled'))]

    #    def get_plugins_as_elements(self, category):
    #        tree = self._tree.find('plugins')
    #        cat = tree.find(category)
    #        if cat is not None:
    #            return cat.findall('plugin')
    def get_global(self, tag):
        root = self.get_root()
        elem = root.find('globals')
        if elem is not None:
            g = elem.find(tag)
            if g is not None:
                return g.text.strip()

    def get_plugin_groups(self, elem=False):
        plugin = self.get_root().find('plugins')
        return [t if elem else t.tag for t in list(plugin)]

    def get_plugin_group(self, name):
        return next((p for p in self.get_plugin_groups(elem=True)
                     if p.tag == name
                    ), None)

    def get_groups(self):
        tree = self.get_root()
        #        root = tree.getroot()
        return [t.tag for t in list(tree)]

    def get_parameters(self, *args, **kw):
        return self._get_parameters(all_=True, *args, **kw)

    def get_parameter(self, subtree, name, all_=True, **kw):
        pa = self._get_parameters(subtree, name, all_=all_, **kw)
        if pa:
            return pa[0]

    def enable_manager(self, name, parent):
        plugin = self.get_plugin(parent)
        man = next((m for m in plugin.findall('manager') if m.text.strip() == name), None)
        man.set('enabled', 'true')
        self.save()

    def disable_manager(self, name, parent):
        plugin = self.get_plugin(parent)
        man = next((m for m in plugin.findall('manager') if m.text.strip() == name), None)
        man.set('enabled', 'false')
        self.save()

    def enable_device(self, name, plugin):
        dev = self.get_device(plugin, name, None, element=True)
        dev.set('enabled', 'true')
        self.save()

    def disable_device(self, name, plugin):
        dev = self.get_device(plugin, name, None, element=True)
        dev.set('enabled', 'false')
        self.save()

    def enable_plugin(self, name, category=None):
        plugin = self.get_plugin(name, category)
        plugin.set('enabled', 'true')
        self.save()

    def disable_plugin(self, name, category=None):
        plugin = self.get_plugin(name, category)
        plugin.set('enabled', 'false')
        self.save()

    def get_flags(self, manager, **kw):
        return self._get_parameters(manager, 'flag', **kw)

    def get_timed_flags(self, manager, **kw):
        return self._get_parameters(manager, 'timed_flag', **kw)

    def get_valve_flags(self, manager, **kw):
        return self._get_parameters(manager, 'valve_flag', **kw)

    def get_rpc_params(self, manager):
        if isinstance(manager, tuple):
            manager = self.get_manager(*manager)

        text = lambda x: x.text.strip() if x is not None else None
        try:
            rpc = manager.find('rpc')
            mode = rpc.get('mode')
            port = text(rpc.find('port'))
            host = text(rpc.find('host'))
            return mode, host, int(port),
        except Exception, e:
            pass

        return None, None, None

    def get_device(self, manager, devname, plugin, element=False):
        if plugin is None:
            man = self.get_plugin(manager)
        else:
            man = self.get_manager(manager, plugin)

        if man is None:
            man = self.get_plugin_group(manager)

        dev = next((d for d in man.findall('device')
                    if d.text.strip() == devname), None)
        if not element and dev:
            dev = dev.text.strip()
        return dev

    def get_devices(self, manager, **kw):
        return self._get_parameters(manager, 'device', **kw)

    def get_processor(self, manager, **kw):
        p = self._get_parameters(manager, 'processor', **kw)
        if p:
            return p[0]

    def get_processors(self):
    #        ps = []
    #        for p in self.get_plugins('Hardware'):
    #            pp = self.get_processor(p)
    #            if pp:
    #                ps.append(pp)
        pl = self.get_plugin_group('hardware')
        ps = [pi for pi in [self.get_processor(p)
                            for p in self.get_plugins('hardware', element=True)] if pi]
        nps = self._get_parameters(pl, 'processor')
        if nps:
            ps += nps
        return ps

    def get_server(self, manager, **kw):
        p = self._get_parameters(manager, 'server', **kw)
        if p:
            return p[0]

    def get_servers(self):
        servers = [pi for pi in [self.get_server(p)
                                 for p in self.get_plugins('hardware', element=True)] if pi]
        h = self.get_plugin_group('hardware')
        if h is not None:
            hs = self._get_parameters(h, 'server')
            if hs:
                servers += hs
        return servers

    def _get_parameters(self, subtree, tag, all_=False, element=False):

        return [d if element else d.text.strip()
                for d in subtree.findall(tag)
                if all_ or to_bool(d.get('enabled'))]

    def get_managers(self, elem, all_=False, element=False):
        return [m if element else m.text.strip()
                for m in elem.findall('manager')
                if all_ or to_bool(m.get('enabled'))]

    def get_plugin(self, name, category=None):
        if '_' in name:

            if 'co2' in name:
                name = name.split('_')[0].capitalize() + 'CO2'
            elif 'uv' in name:
                name = name.split('_')[0].capitalize() + 'UV'
            else:
                name = ''.join([a.capitalize() for a in name.split('_')])
        else:
            name = name[0].upper() + name[1:]

        return self._get_element(category, name)

    def get_manager(self, name, plugin):

        if 'Manager' in plugin:
            plugin = plugin.replace('Manager', '')
        p = self.get_plugin(plugin)

        man = next((pi for pi in p.findall('manager') if pi.text.strip() == name), None)

        return man

    def get_categories(self):
        root = self.get_root()
        tree = root.find('plugins')
        s = lambda x: x.tag

        cats = map(s, [c for c in tree.iter(Element)])
        return list(set(cats))
        #return map(s, set([c for c in tree.iter()]))

    def _get_element(self, category, name, tag='plugin'):
        root = self.get_root()
        tree = root.find('plugins')

        if category is None:
            iterator = lambda: tree.iter(tag=tag)
        #            return next((p for p in tree.iter(tag=tag) if p.text.strip() == name), None)
        #            for p in tree.iter(tag=tag):
        #                if p.text.strip() == name:
        #                    return p
        else:
            cat = tree.find(category)
            if cat is not None:
                iterator = lambda: cat.findall(tag)
            else:
                iterator = lambda: ''
                #            for plugin in cat.findall(tag):
                #                if plugin.text.strip() == name:
                #                    return plugin
        return next((p for p in iterator() if p.text.strip() == name), None)

    def get_systems(self):
        p = self.get_plugin('ExtractionLine')
        if p is not None:
            return [(s.text.strip(), s.get('master_host')) for s in p.findall('system')]
        return []

        #    def get_processors(self):

#
#        cat = self._tree.find('remotehardware')
#        pi = None
#        if cat is not None:
#            pi = cat.findall('processor')
#
#        return [pii.text.strip() for pii in (pi if pi else [])]
#============= EOF =============================================
