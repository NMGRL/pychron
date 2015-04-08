#!/usr/bin/python
# ===============================================================================
# Copyright 2015 Jake Ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
# ============= standard library imports ========================
# ============= local library imports  ==========================
from ConfigParser import ConfigParser
import os
import pickle

import lxml.etree as etree


class App(object):
    _commands = ('exit', 'help', 'valve', 'connection', 'valves', 'actuator')

    _valve_path = None
    _canvas_path = None

    _valve_parser = None
    _canvas_parser = None
    _translation_gen = None

    def start(self):
        print '=========================================================='
        print '=====================          ==========================='
        print '=========================================================='
        print '========================    =============================='
        print '=====================          ==========================='
        print '==================                 ======================='
        print ''
        print '======= Welcome to the Extraction Line Setup script ======'
        print ''
        print '==================                 ======================='
        print '=====================          ==========================='
        print '========================    =============================='
        print '=========================================================='
        print '==================                 ======================='
        print '=========================================================='

        if not self._load_config():
            self._default_config()

        self._translation_gen = self._get_translation()
        while 1:
            cmd = self._get_command()
            if not self._process(cmd):
                break

        self._dump()
        self._dump_config()
        print 'Good bye'

    def _dump(self):
        for par, path in ((self._get_valve_parser(), self._valve_path),
                          (self._get_canvas_parser(), self._canvas_path)):
            par.write(path, pretty_print=True, method='xml', xml_declaration=True, )

    def _default_config(self):
        print ''
        print '------- Load default configuration ------'
        print ''
        home = os.path.expanduser('~')
        p = os.path.join(home, '.pychron', 'elsetup.p')
        with open(p, 'w') as wfile:
            vp = os.path.join(self.setupfiles, 'extractionline', 'valves.xml')
            use_default = raw_input('Use default valve file: {}. [y]/n '.format(vp))
            if use_default not in ('y', 'Y', 'yes', ''):
                vp = raw_input('Enter path to valve file: ')
                vp = os.path.join(self.root, vp)
            self._valve_path = vp

            vp = os.path.join(self.setupfiles, 'canvas2D', 'canvas.xml')
            use_default = raw_input('Use default valve file: {}. [y]/n '.format(vp))
            if use_default not in ('y', 'Y', 'yes', ''):
                vp = raw_input('Enter path to canvas file: ')
                vp = os.path.join(self.root, vp)
            self._canvas_path = vp

            yd = {k: getattr(self, k) for k in ('_valve_path', '_canvas_path')}
            pickle.dump(yd, wfile)

    def _dump_config(self):
        home = os.path.expanduser('~')
        p = os.path.join(home, '.pychron', 'elsetup.p')
        with open(p, 'w') as wfile:
            yd = {k: getattr(self, k) for k in ('_valve_path', '_canvas_path')}
            pickle.dump(yd, wfile)

    def _load_config(self):
        p = os.path.join(os.path.expanduser('~'), '.pychron', 'elsetup.p')
        if os.path.isfile(p):
            a = raw_input('Load previous configuration? [y]/n ')
            if a.lower() in ('y', 'yes', ''):
                print 'Loading configuration from: {}'.format(p)
                with open(p, 'r') as rfile:
                    try:
                        yd = pickle.load(rfile)
                        for k, v in yd.items():
                            setattr(self, k, v)
                        return True
                    except:
                        pass

    def _get_command(self):

        while 1:
            cmd = raw_input('Enter a command: ')
            if cmd not in self._commands:
                print '{} is not a valid command'.format(cmd)
                self._help()
            else:
                return cmd

    def _process(self, cmd):
        self._enter_mode(cmd.capitalize())
        func = getattr(self, '_{}'.format(cmd))
        r = func()
        self._exit_mode()
        return r

    @property
    def root(self):
        home = os.path.expanduser('~')
        root = os.path.join(home, 'Pychron')
        return root

    @property
    def setupfiles(self):
        return os.path.join(self.root, 'setupfiles')

    @property
    def droot(self):
        return os.path.join(self.root, 'devices')

    # commands
    def _help(self):
        print '-------- Valid commands --------'
        print '\n'.join(map('\t{}'.format, self._commands))
        print '--------------------------------'
        return True

    def _exit(self):
        return

    def _view(self):
        pass

    def _actuator(self):
        while 1:
            name = raw_input('Enter name of actuator: ')
            p = os.path.join(self.droot, '{}.cfg'.format(name))

            cfg = ConfigParser()
            cfg.add_section('General')

            dtype = raw_input('Enter device type: ')
            cfg.set('General', 'type', dtype)

            dcfg = ConfigParser()
            dcfg.add_section('General')
            com = 'Communications'
            dcfg.add_section(com)

            kind = self._get_comms_kind()
            dcfg.set(com, 'kind', kind)
            port = self._get_port(kind)
            dcfg.set(com, 'port', port)

            dp = os.path.join(self.droot, '{}.cfg'.format(dtype))
            with open(dp, 'w') as wfile:
                dcfg.write(wfile)

            with open(p, 'w') as wfile:
                cfg.write(wfile)

            if not self._get_yes('Add another actuator'):
                break

        return True

    def _connection(self):
        canvas_parser = self._get_canvas_parser()
        while 1:

            root = canvas_parser.getroot()
            con = etree.SubElement(root, 'connection')
            while 1:
                orient = raw_input('Enter orientation [h]/v: ')
                if orient not in ('h', 'v', ''):
                    print 'Invalid orientation. use "h",or "v"'
                else:
                    if orient == '':
                        orient = 'h'
                    break
            con.attrib['orientation'] = 'horizontal' if orient == 'h' else 'vertical'
            for attr in ('start', 'end'):
                name = raw_input('Enter {}: '.format(attr))
                if name != '':
                    s = etree.SubElement(con, attr)
                    s.text = name
                    offset = raw_input('Enter offset: ')
                    if offset:
                        s.attrib['offset'] = offset

            if not self._get_yes('Add another connection?'):
                break

        return True

    def _valves(self):
        while 1:

            names = raw_input('Enter list of valve names (e.g. A,B,C): ')
            for name in names.split(','):
                if not self._has_valve(name):
                    self._add_valve(name, 'Empty Description')

            if not self._get_yes('Add another set of valves?'):
                break

        return True

    def _valve(self):
        self._enter_mode('Valve')
        while 1:
            while 1:
                # name = 'A'
                name = raw_input('Enter Short name of valve (e.g. A): ')
                if self._has_valve(name):
                    continue

                # desc = 'Laser to Turbo'
                desc = raw_input('Enter Description of valve (e.g. Laser to Turbo): ')
                break

            vv, cv = self._add_valve(name, desc)
            act = raw_input('Enter actuator name: ')
            if act:
                add = True
                p = os.path.join(self.droot, '{}.cfg'.format(act))
                if not os.path.isfile(p):
                    msg = 'Not a valid actuator {}. Add anyway'
                    add = self._get_yes(msg)

                if add:
                    ea = etree.SubElement(vv, 'actuator')
                    ea.text = act

            # aa = raw_input('Add another valve? [y]/n ')
            if self._get_yes('Add another valve?'):
                break
                # if aa.lower() not in ('y', 'yes', ''):
                # break

        return True

    # helpers
    def _get_port(self, kind):
        while 1:
            port = raw_input('Enter a port: ')
            if kind == 'serial':
                # check if this is a valid port
                if os.path.isfile(os.path.join('/', 'dev', port)):
                    return port
                elif self._get_yes('Not a valid port {}. Add anyway'.format(port)):
                    return port

            elif kind == 'ethernet':
                if not port:
                    port = 8000

                try:
                    port = int(port)
                    return port
                except ValueError:
                    print 'Invalid port {} for this kind {}'.format(port, kind)

    def _get_comms_kind(self):
        kinds = ('serial', 'ethernet')
        while 1:

            kind = raw_input('Enter a communication kind ({}) [serial]: '.format(','.join(kinds)))
            if not kind:
                kind = 'serial'

            if kind not in kinds:
                print 'Invalid kind {}: use: {}'.format(kind, ','.join('kinds'))
            else:
                return kind

    def _has_valve(self, name):
        valve_parser = self._get_valve_parser()
        root = valve_parser.getroot()
        for elem in root.iter('valve'):
            if elem.text == name:
                print 'Valve {} already exists. '.format(name)
                return True

    def _add_valve(self, name, desc):
        valve_parser = self._get_valve_parser()
        canvas_parser = self._get_canvas_parser()

        root = valve_parser.getroot()
        vv = etree.SubElement(root, 'valve')
        vv.text = name
        dv = etree.SubElement(vv, 'description')
        dv.text = desc

        root = canvas_parser.getroot()
        cv = etree.SubElement(root, 'valve')
        cv.text = name
        t = etree.SubElement(cv, 'translation')
        t.text = self._translation_gen.next()
        return vv, cv

    def _get_yes(self, msg):
        is_yes = raw_input('{} [y]/n: '.format(msg))
        return is_yes.lower() in ('y', 'yes', '')

    def _get_translation(self):
        r = 4
        c = 8
        ro = r / 2
        co = c / 2
        for i in range(r):
            for j in range(c):
                yield '{},{}'.format(i - ro, j - co)

    def _get_valve_parser(self):
        if self._valve_parser is None:
            if os.path.isfile(self._valve_path):
                tree = etree.parse(self._valve_path)
            else:
                tree = etree.ElementTree(etree.Element('root'))
            tree = etree.ElementTree(etree.Element('root'))

            self._valve_parser = tree
        return self._valve_parser

    def _get_canvas_parser(self):
        if self._canvas_parser is None:
            if os.path.isfile(self._canvas_path):
                tree = etree.parse(self._canvas_path)
            else:
                tree = etree.ElementTree(etree.Element('root'))
            tree = etree.ElementTree(etree.Element('root'))

            self._canvas_parser = tree

        return self._canvas_parser

    def _enter_mode(self, name):
        print ''
        print '=========================================================='
        print 'MODE:{:>15s}'.format(name)
        print '=========================================================='
        print ''

    def _exit_mode(self):
        print '=========================================================='
        print ''


def main():
    a = App()
    a.start()


if __name__ == '__main__':
    main()

# ============= EOF =============================================



