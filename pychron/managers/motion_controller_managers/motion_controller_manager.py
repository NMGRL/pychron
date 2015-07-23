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
from traits.api import Instance, Enum, DelegatesTo, Property, Button, Any, Float
from traitsui.api import View, Item, HGroup, spring, \
    ListEditor, VGroup, UItem
# =============standard library imports ========================

# =============local library imports  ==========================
from pychron.managers.manager import Manager
from pychron.hardware.motion_controller import MotionController
from pychron.paths import paths
from pychron.core.helpers.filetools import parse_file


class MotionControllerManager(Manager):
    """
    """

    motion_controller = Instance(MotionController)
    _axes = DelegatesTo('motion_controller', prefix='axes')
    axes = Property

    apply_button = Button('Apply')
    read_button = Button('Read')
    load_button = Button('Load')
    # print_param_table = Button('Print')

    motion_group = DelegatesTo('motion_controller', prefix='groupobj')

    view_style = Enum('simple_view', 'full_view')

    selected = Any
    xmove_to_button = Button('Move X')
    ymove_to_button = Button('Move Y')
    xtarget_position = Float
    ytarget_position = Float

    def kill(self, **kw):
        super(MotionControllerManager, self).kill(**kw)
        self.motion_controller.save_axes_parameters()

    def _get_axis_by_id(self, aid):
        return next((a for a in self._axes.itervalues() if a.id == int(aid)), None)

    def _get_axes(self):
        keys = self._axes.keys()
        keys.sort()
        axs = [self._axes[k] for k in keys]
        if self.motion_group:
            axs += [self.motion_group]
        return axs

    def _get_selected(self):
        ax = self.selected
        if ax is None:
            ax = self.axes[0]

        return ax

    # handlers
    def _xmove_to_button_fired(self):
        ax = self.motion_controller.axes['x']
        self.motion_controller.ask('{}PA{}'.format(ax.id, self.xtarget_position))

    def _ymove_to_button_fired(self):
        ax = self.motion_controller.axes['y']
        self.motion_controller.ask('{}PA{}'.format(ax.id, self.ytarget_position))

    def _read_button_fired(self):
        ax = self._get_selected()
        ax._read_parameters_fired()

    def _apply_button_fired(self):
        ax = self._get_selected()
        print ax, ax.id
        if ax is not None:
            ax.upload_parameters_to_device()

        self.motion_controller.save_axes_parameters(axis=ax)

    def _load_button_fired(self):
        path = self.open_file_dialog(default_directory=paths.device_dir)
        # path = os.path.join(root_dir, 'zobs', 'NewStage-Axis-1.txt')
        if path is not None:

            # sniff the file to get the axis
            lines = parse_file(path)

            aid = lines[0][0]
            try:
                ax = self._get_axis_by_id(aid)
                func = ax.load_parameters_from_file
            except ValueError:
                # this is a txt file not a cfg
                ax = self._get_selected()
                if ax is not None:
                    func = ax.load

            if ax is not None:
                func(path)
                # ax.load_parameters_from_file(path)
                # ax.load_parameters_from_file(path)

    def traits_view(self):
        """
        """
        cgrp = VGroup(Item('axes',
                           style='custom',
                           show_label=False,
                           editor=ListEditor(use_notebook=True,
                                             dock_style='tab',
                                             page_name='.name',
                                             selected='selected',
                                             view='full_view')),
                      HGroup(spring, Item('load_button'),
                             Item('read_button'),
                             Item('apply_button'),
                             show_labels=False))

        tgrp = VGroup(HGroup(UItem('xmove_to_button'), UItem('xtarget_position')),
                      HGroup(UItem('ymove_to_button'), UItem('ytarget_position')))

        view = View(VGroup(tgrp, cgrp),
                    resizable=True,
                    handler=self.handler_klass,  # MotionControllerManagerHandler,
                    title='Configure Motion Controller')
        return view

    def configure_view(self):
        v = View(Item('axes',
                      style='custom',
                      show_label=False,
                      editor=ListEditor(use_notebook=True,
                                        dock_style='tab',
                                        page_name='.name',
                                        view=self.view_style,
                                        selected='selected'
                                        )),
                 HGroup(spring, Item('load_button'),
                        Item('read_button'), Item('apply_button'), show_labels=False, ))
        return v
        #        print [self._axes[k] for k in keys] + [self.motion_group]
        #        return [self._axes[k] for k in keys] + [self.motion_group]

        #    def _restore_fired(self):
        #        '''
        #        '''
        #        self.motion_controller.axes_factory()
        #        self.trait_property_changed('axes', None)
        #        for a in self.axes:
        #            a.load_

        #    def _apply_all_fired(self):
        #        '''
        #        '''
        # #        for a in self.axes:
        # #            a.upload_parameters_to_device()
        #        if sele
        # #        self.motion_controller.save()
        # def _print_param_table_fired(self):
        #         table = []
        #         for a in self.axes:
        #             attrs, codes, params = a.load_parameters()
        #             table.append(params)
        #
        #         try:
        #             p = '/Users/ross/Sandbox/unidex_dump.txt'
        #             with open(p, 'w') as f:
        #                 for attr, code, ri in zip(attrs, codes, zip(*table)):
        #                     l = ''.join(map('{:<20s}'.format, map(str, ri)))
        #                     l = '{:<20s} {} - {}'.format(attr, code, l)
        #                     f.write(l + '\n')
        #                     print l
        #         except Exception, e:
        #             print 'exception', e
