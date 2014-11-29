# ===============================================================================
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
# ===============================================================================

# =============enthought library imports=======================
from traits.api import Str, Float, Any, Button, Int, List, Bool, Property
from traitsui.api import Item, HGroup, VGroup, \
    ButtonEditor, spring
from pyface.api import FileDialog, OK, DirectoryDialog
# =============standard library imports ========================
import os
from threading import Thread
import time
# =============local library imports  ==========================
from pychron.viewable import Viewable, ViewableHandler
from pychron.rpc.rpcable import RPCable
from pychron.saveable import SaveableHandler


class MassSpecParam(object):
    _value = None

    def __init__(self, value):
        self._value = value

    def get(self):
        return self._value


class ManagerHandler(ViewableHandler):
    '''
        
    '''

    def init(self, info):
        info.object.initialized = True
        super(ManagerHandler, self).init(info)

    #    def closed(self, info, is_ok):
    #        '''
    #        '''
    #        super(ManagerHandler, self).closed(info, is_ok)
    #        info.object.kill()
    #        try:
    #            MANAGERS.remove(info.object)
    #            info.object.application.uis.remove(info.ui)
    #        except ValueError:
    #            pass
    #
    # #        import gc
    # #        gc.collect()
    #
    #        return True

    def close(self, info, isok):
        info.object.close(isok)
        return True


class AppHandler(ManagerHandler):
    def closed(self, info, isok):
        info.object.kill()
        from pychron.displays.gdisplays import gLoggerDisplay, gWarningDisplay, gMessageDisplay
        gLoggerDisplay.close_ui()
        gWarningDisplay.close_ui()
        gMessageDisplay.close_ui()

        return True


class SaveableManagerHandler(SaveableHandler, ManagerHandler):
    pass


class Manager(Viewable, RPCable):
    """
    """

    test = Button

    macro = None
    parent = Any

    title = Str
    window_x = Float(0.1)
    window_y = Float(0.1)
    window_width = Float(0.75)
    window_height = Float(0.75)
    simulation = Property

    _killed = False
    enable_close_after = Bool
    close_after_minutes = Int  # in minutes

    handler_klass = ManagerHandler
    application = Any

    devices = List
    flags = List

    initialized = False

    _mass_spec_params = None

    error_code = None

    def finish_loading(self):
        """
        """
        pass

    def opened(self, ui):
        def _loop():
            start = time.time()
            self.info('Window set to close after {} min'.format(self.close_after_minutes))

            now = time.time()
            while now - start < (self.close_after_minutes * 60) and not self._killed:
                time.sleep(1)
                now = time.time()

            self.close_ui()

        if self.enable_close_after and self.close_after_minutes:
            t = Thread(target=_loop)
            t.start()

        self._killed = False
        for _k, man in self.get_managers():
            man._killed = False

        self.add_window(ui)

    def add_window(self, ui):

        try:
            if self.application is not None:
                self.application.uis.append(ui)
        except AttributeError:
            pass

    def open_view(self, obj, **kw):
        def _open():
            ui = obj.edit_traits(**kw)
            self.add_window(ui)

        from pychron.core.ui.gui import invoke_in_main_thread
        invoke_in_main_thread(_open)

    def kill(self, **kw):
        """

        """

        if not self._killed:
            self.info('killing')
            self._kill_hook()

            self._killed = True

            for _k, man in self.get_managers():
                if man is not None:
                    if hasattr(man, 'kill'):
                        man.kill()

    def open_file_dialog(self, **kw):
        """
        """
        return self._file_dialog('open', **kw)

    def save_file_dialog(self, **kw):
        """
        """
        return self._file_dialog('save as', **kw)

    def open_directory_dialog(self, **kw):
        return self._directory_dialog(False, **kw)

    def save_directory_dialog(self, **kw):
        return self._directory_dialog(True)

    def get_error(self):
        e = self.error_code
        self.error_code = None
        return str(e)

    def get_managers(self):

        return [(ma, getattr(self, ma)) for ma in self.traits()
                if ma.endswith('_manager')
                and getattr(self, ma) is not None]

    def get_device(self, device_name):
        """
        """
        from pychron.hardware.core.i_core_device import ICoreDevice

        dev = None
        if hasattr(self, device_name):
            dev = getattr(self, device_name)
        elif hasattr(self.parent, device_name):
            dev = getattr(self.parent, device_name)
        else:

            for man in self.get_managers():
                if hasattr(man, device_name):
                    dev = getattr(man, device_name)
                    break

            if self.application:
                dev = self.application.get_service(ICoreDevice, 'name=="{}"'.format(device_name))

            if dev is None:
                self.warning('Invalid device {}'.format(device_name))

        return dev

    def get_default_managers(self):
        return []

    def get_manager_factory(self, package, klass, warn=True):
        #        print package, klass
        class_factory = None
        try:
            m = __import__(package, globals(), locals(), [klass], -1)
            class_factory = getattr(m, klass)
        except ImportError:
            if warn:
                self.warning(' Invalid manager class {} {}'.format(package, klass))

        except:
            if warn:
                self.warning('Problem with manager class {} source'.format(klass))

        return class_factory

    # ===============================================================================
    #  flags
    # ===============================================================================
    def add_flag(self, f):
        from pychron.hardware.flag import Flag

        ff = Flag(f)
        self.flags.append(ff)
        if self.application:
            fm = self.application.get_service('pychron.hardware.flag_manager.FlagManager')
            if fm is not None:
                fm.add_flag(ff)

    def add_valve_flag(self, f, v):
        #         from pychron.hardware.flag import TimedFlag
        from pychron.hardware.flag import ValveFlag

        ff = ValveFlag(f, valves=v, manager=self)
        self.flags.append(ff)
        if self.application:
            fm = self.application.get_service('pychron.hardware.flag_manager.FlagManager')
            if fm is not None:
                fm.add_valve_flag(ff)

    def add_timed_flag(self, f):
        from pychron.hardware.flag import TimedFlag

        ff = TimedFlag(f)
        self.flags.append(ff)
        if self.application:
            fm = self.application.get_service('pychron.hardware.flag_manager.FlagManager')
            if fm is not None:
                fm.add_timed_flag(ff)

    def get_mass_spec_param(self, name):
        from pychron.paths import paths

        cp = self._mass_spec_params
        if cp is None:
            # open the mass spec parameters file
            cp = self.configparser_factory()
            cp.read(os.path.join(paths.setup_dir, 'mass_spec_params.cfg'))
        try:
            v = cp.get('General', name)
            return MassSpecParam(v)
        except Exception:
            pass
            #        return

            #        return next((f for f in self.flags if f.name == name), None)

    def get_flag(self, name):
        return next((f for f in self.flags if f.name == name), None)

    def set_flag(self, name):
        return self._set_flag(name, True)

    def clear_flag(self, name):
        return self._set_flag(name, False)

    def create_manager(self, manager, **kw):
        """
        """
        klass = self.convert_config_name(manager)
        params = dict(name=manager)
        params['parent'] = self
        params['application'] = self.application

        return self._create_manager(klass, manager, params, **kw)

    def create_device(self, device_name, gdict=None, dev_class=None,
                      prefix=None, obj=None):
        """
        """
        device = None

        if dev_class is not None:
            klass = dev_class
        else:
            klass = self.convert_config_name(device_name)

        if gdict is not None and klass in gdict:
            class_factory = gdict[klass]

        else:
            from pychron.hardware import HW_PACKAGE_MAP

            try:
                package = HW_PACKAGE_MAP[klass]
                m = __import__(package, globals(), locals(), [klass], -1)
                class_factory = getattr(m, klass)

            except ImportError:
                import traceback

                traceback.print_exc()
                self.warning('Invalid device class {}'.format(klass))
                return

        device = class_factory(name=device_name)
        if obj is not None:
            device.copy_traits(obj, traits=['configuration_dir_name'])

        if device is not None:
            if prefix:
                device_name = ''.join((prefix, device_name))

            if device_name in self.traits():
                self.trait_set(**{device_name: device})
            else:
                self.add_trait(device_name, device)

        return device

    # private
    def _set_flag(self, name, val):
        flag = self.get_flag(name)
        if flag is not None:
            flag.set(val)
            return True

    def _kill_hook(self):
        pass

    def _create_manager(self, klass, manager, params,
                        port=None, host=None, remote=False):
        from pychron.managers import manager_package_dict

        if remote:
            klass = 'Remote{}'.format(klass)
            params['rpc_port'] = port
            params['rpc_host'] = host

        try:
            package = manager_package_dict[klass]
            class_factory = self.get_manager_factory(package, klass)
            if class_factory:
                m = class_factory(**params)

                self.add_trait(manager, m)
                return m

        except KeyError, e:
            print 'create manager', e
            pass

    def _directory_dialog(self, new_directory, **kw):
        dlg = DirectoryDialog(new_directory=new_directory, **kw)
        if dlg.open() == OK:
            return dlg.path

    def _file_dialog(self, action, **kw):
        """
        """
        #         print 'file_dialog', kw
        dlg = FileDialog(action=action, **kw)
        if dlg.open() == OK:
            return dlg.path

    def _get_simulation(self):
        return False

    # view factories
    def _button_factory(self, name, label=None, enabled=None, align=None, **kw):
        """

        """
        b = Item(name, show_label=False, **kw)

        if label is None:
            label = '{}_label'.format(name)

        if label is not None:
            b.editor = ButtonEditor(label_value=label)

        if enabled is not None:
            b.enabled_when = enabled

        if align is not None:
            if align == 'right':
                b = HGroup(spring, b)
            elif align == 'center':
                b = HGroup(spring, b, spring)
            else:
                b = HGroup(b, spring)

        return b

    def _button_group_factory(self, buttons, orientation='v'):
        """
        """
        vg = VGroup() if orientation == 'v' else HGroup()

        for name, label, enabled in buttons:
            vg.content.append(HGroup(self._button_factory(name, label, enabled), springy=False))
        return vg
# =================== EOF =================================================

    # def _led_factory(self, name, color='green'):
    #     """
    #
    #     """
    #     i = Item(name, show_label=False)
    #     return i

    # def _switch_factory(self, name, label=False, enabled=None):
    #     '''
    #     '''
    #     if label == True:
    #         label = '{}_label'.format(name)
    #
    #     v = VGroup(HGroup(spring, Label(name.upper()), spring),
    #              HGroup(spring, self._led_factory('{}_led'.format(name)), spring),
    #              self._button_factory(name, label, enabled)
    #              )
    #     return v
    #
    # def _switch_group_factory(self, switches, orientation='h', **kw):
    #     '''
    #
    #     '''
    #     if orientation == 'h':
    #         g = HGroup(**kw)
    #     else:
    #         g = VGroup(**kw)
    #
    #     for s, label, enabled in switches:
    #         sw = self._switch_factory(s, label=label, enabled=enabled)
    #         g.content.append(sw)
    #     return g
    #
    # def _scrubber_factory(self, name, range_dict):
    #     '''
    #
    #     '''
    #     return Item(name, editor=ScrubberEditor(**range_dict))
    #
    # def _scrubber_group_factory(self, scrubbers, **kw):
    #     '''
    #
    #
    #     '''
    #     vg = VGroup(**kw)
    #     for name, prefix in scrubbers:
    #         range_dict = dict(low=getattr(self, '%smin' % prefix), high=getattr(self, '%smax' % prefix))
    #         vg.content.append(self._scrubber_factory(name, range_dict))
    #     return vg
    #
    # def _readonly_slider_factory(self, *args, **kw):
    #     '''
    #
    #     '''
    #     return self._slider_factory(
    #         enabled_when='0',
    #         *args, **kw)
    #
    # def _slider_factory(self, name, prefix, mode='slider', **kw):
    #     '''
    #     '''
    #     return Item(name, editor=RangeEditor(mode=mode,
    #                                          low_name='%smin' % prefix,
    #                                          high_name='%smax' % prefix,
    #
    #                                          format='%0.2f'
    #     ),
    #
    #                 **kw)
    #
    # def _update_slider_factory(self, name, prefix, **kw):
    #     '''
    #
    #     '''
    #     vg = VGroup()
    #
    #     r = self._slider_factory(name, prefix, **kw)
    #     vg.content.append(r)
    #
    #     ur = self._slider_factory('update_%s' % name, name, show_label=False, enabled_when='0')
    #
    #     vg.content.append(ur)
    #
    #     return vg
    #
    # def _update_slider_group_factory(self, sliders, **kw):
    #     '''
    #
    #     '''
    #     vg = VGroup(**kw)
    #
    #     for si, prefix, options in sliders:
    #         if not options:
    #             options = {}
    #         vg.content.append(self._update_slider_factory(si, prefix, **options))
    #     return vg
    #
    # def _slider_group_factory(self, sliders, **kw):
    #     '''
    #
    #     '''
    #     vg = VGroup(**kw)
    #     for si, prefix, options in sliders:
    #         if not options:
    #             options = {}
    #         vg.content.append(self._slider_factory(si, prefix, **options))
    #     return vg
    # def get_menus(self):
    #     '''
    #     '''
    #     pass
    #
    # def _menu_factory(self, name, actions):
    #     '''
    #     '''
    #     a = [Action(**a) for a in actions]
    #     return Menu(name=name, *a)
    #
    # def menus_factory(self):
    #     '''
    #     '''
    #     menus = self.get_menus()
    #     if menus:
    #         return [self._menu_factory(m, actions) for m, actions in menus]
    #
    # def _menubar_factory(self):
    #     '''
    #     '''
    #
    #     menus = self.menus_factory()
    #     return MenuBar(*menus)


