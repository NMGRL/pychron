# ===============================================================================
# Copyright 2016 Jake Ross
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
import os
from configparser import ConfigParser, RawConfigParser
import yaml
# ============= local library imports  ==========================
from pychron.core.codetools.inspection import caller
from pychron.core.yaml import yload
from pychron.paths import paths


class YAMLParser:
    def __init__(self, obj):
        self._obj = obj

    def write(self, fp):
        yaml.dump(self._obj, fp)

    def has_section(self, section):
        return self._obj.get(section)

    def has_option(self, section, option):
        try:
            return self._obj[section][option]
        except KeyError:
            pass

    def options(self, section):
        d = self._obj.get(section)
        return d.keys()

    def get(self, section, option):
        s = self._obj.get(section)
        return s.get(option)

    def getfloat(self, *args, **kw):
        return float(self.get(*args, **kw))

    def getint(self, *args, **kw):
        return int(self.get(*args, **kw))

    def getboolean(self, *args, **kw):
        return bool(self.get(*args, **kw))


class ParserWrapper:
    _parser = None

    def read(self, path):
        if path.endswith('.cfg'):
            p = ConfigParser()
            p.read(path)
        else:
            with open(path, 'r') as rfile:
                p = yload(rfile)
                p = YAMLParser(p)

        self._parser = p

    def __getattr__(self, item):
        return getattr(self._parser, item)


class ConfigMixin:
    configuration_dir_name = None
    configuration_dir_path = None
    configuration_name = None
    config_path = None

    def configparser_factory(self):
        return ParserWrapper()

    def config_get_options(self, config, section):
        r = []
        if config.has_section(section):
            r = config.options(section)
        return r

    def config_get(self, config, section, option,
                   cast=None,
                   optional=False,
                   default=None):

        if cast is not None:
            func = getattr(config, 'get{}'.format(cast))
        else:
            func = config.get

        if not config.has_option(section, option):
            if not optional:
                if self.logger is not None:
                    self.warning('Need to specifiy {}:{}'.format(section,
                                                                 option))

            return default
        else:
            return func(section, option)

    def set_attribute(self, config, attribute, section, option, **kw):
        r = self.config_get(config, section, option, **kw)
        if r is not None:
            setattr(self, attribute, r)

    def write_configuration(self, config, path=None):

        if path is None:
            path = self.config_path

        with open(path, 'w') as f:
            config.write(f)

    def get_configuration(self, path=None, name=None, warn=True, set_path=True):

        if path is None:
            path = self.config_path
            if path is None:
                device_dir = paths.device_dir

                if self.configuration_dir_name:
                    base = os.path.join(device_dir,
                                        self.configuration_dir_name)
                else:
                    base = device_dir

                self.configuration_dir_path = base
                if name is None:
                    name = self.configuration_name
                    if name is None:
                        name = self.name

                path = os.path.join(base, '{}.yaml'.format(name))
                if not os.path.isfile(path):
                    path = os.path.join(base, '{}.yml'.format(name))
                    if not os.path.isfile(path):
                        path = os.path.join(base, '{}.cfg'.format(name))

        if path is not None and os.path.isfile(path):
            config = self.configparser_factory()
            self.debug('loading configuration from {}'.format(path))
            config.read(path)
            if set_path:
                self.config_path = path
            return config
        elif warn:
            msg = '{} not a valid initialization file'.format(path)
            self.debug(msg)
            self.warning_dialog(msg)

    def get_configuration_writer(self, p=None):
        config = ParserWrapper()
        if p:
            config.read(p)

        return config

# ============= EOF =============================================
