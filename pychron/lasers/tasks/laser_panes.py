#===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import Property
from traitsui.api import View, UItem, Group, InstanceEditor, HGroup, \
    EnumEditor, Item, spring, Spring, ButtonEditor, VGroup, RangeEditor
from pyface.tasks.traits_task_pane import TraitsTaskPane
from pyface.tasks.traits_dock_pane import TraitsDockPane
#============= standard library imports ========================
#============= local library imports  ==========================
from pychron.envisage.tasks.pane_helpers import icon_button_editor
from pychron.experiment.utilities.identifier import pretty_extract_device
from pychron.ui.led_editor import LEDEditor
from enable.component_editor import ComponentEditor
# from pychron.lasers.stage_managers.video_stage_manager import VideoStageManager


def SUItem(name, **kw):
    return UItem('object.stage_manager.{}'.format(name),
                 #                 defined_when='mode!="client"',
                 **kw)


class BaseLaserPane(TraitsTaskPane):
    def traits_view(self):
    #         if self.model.mode!='client':
        v = View(UItem('stage_manager',
                       # defined_when='mode!="client"',
                       style='custom'),
                 HGroup(UItem('status_text', style='readonly'), spring),
                 #                  statusbar='status_text'
        )
        #         else:
        #             v=View()
        return v


class AxesPane(TraitsDockPane):
    name = 'Axes'

    def traits_view(self):
        agrp = SUItem('stage_controller', style='custom')
        return View(agrp)


class StageControlPane(TraitsDockPane):
    name = 'Stage'

    def traits_view(self):
        #=======================================================================
        # convienience functions
        #=======================================================================
        def make_sm_name(name):
            return 'object.stage_manager.{}'.format(name)

        def SItem(name, **kw):
            return Item(make_sm_name(name),
                        #                         defined_when='mode!="client"',
                        **kw)

        def CItem(name, **kw):
            return Item('object.stage_manager.canvas.{}'.format(name),
                        #                         defined_when='mode!="client"',
                        **kw)

        def CUItem(name, **kw):
            return UItem('object.stage_manager.canvas.{}'.format(name),
                         #                         defined_when='mode!="client"',
                         **kw)
            #=======================================================================
            #
            #=======================================================================

        #         agrp = SUItem('stage_controller', style='custom')
        pgrp = Group(
            SUItem('calibrated_position_entry',
                   tooltip='Enter a positon e.g 1 for a hole, or 3,4 for X,Y'
            ),
            label='Calibrated Position',
            show_border=True)
        hgrp = HGroup(SUItem('stop_button'),
                      SUItem('home'),
                      SUItem('home_option', editor=EnumEditor(name='object.stage_manager.home_options'))
        )
        cngrp = VGroup(
            CItem('show_bounds_rect'),
            #                       Item('render_map'),
            CItem('show_grids'),
            HGroup(CItem('show_laser_position'),
                   CUItem('crosshairs_color',
                          #                                   editor=ColorEditor(),
                          #                                    springy=True,
                          #                                    show_label=False
                   )
            ),
            CItem('crosshairs_kind'),
            CItem('crosshairs_radius'),
            HGroup(
                CItem('crosshairs_offsetx', label='Offset'),
                CUItem('crosshairs_offsety')
            ),
            CItem('crosshairs_offset_color'),
            HGroup(CItem('show_desired_position'),
                   CUItem('desired_position_color',
                          #                                     springy=True
                   )
            ),
            label='Canvas'
        )

        #         if self.model.mode != 'client':

        mode = self.model.mode
        #         mvgrp = None
        #         recgrp = None
        cagrp = VGroup(
            visible_when='use_video',
            label='Camera')

        if self.model.stage_manager.__class__.__name__ == 'VideoStageManager':
            mvgrp = VGroup(
                #                       HGroup(SItem('use_autocenter', label='Enabled'),
                #                              SUItem('autocenter_button',
                #                                   enabled_when='use_autocenter'),
                #                              SUItem('configure_autocenter_button')
                #                           ),
                SUItem('autocenter_manager', style='custom'),
                SUItem('autofocus_manager', style='custom'),
                label='Machine Vision', show_border=True,
            )

            recgrp = VGroup(
                HGroup(SItem('snapshot_button', show_label=False),
                       VGroup(SItem('auto_save_snapshot'),
                              SItem('render_with_markup'))),
                SUItem('record', editor=ButtonEditor(label_value=make_sm_name('record_label'))),
                show_border=True,
                label='Recording'
            )
            cfggrp = VGroup(
                SItem('camera_zoom_coefficients', label='Zoom Coefficients')
            )
            cagrp.content.extend((cfggrp, recgrp, mvgrp))
            #         else:
        #             recgrp = Group()

        #         cagrp = VGroup(
        #                        recgrp,
        # #                   label='Machine Vision', show_border=True)
        #                        visible_when='use_video',
        #                        label='Camera'
        #                        )
        #         if mode != 'client' and mvgrp:
        #             cagrp.content.insert(0, co)
        #             cagrp.content.append(mvgrp)

        cgrp = Group(
            SUItem('stage_controller', style='custom',
                   label='Axes'
            ),
            cngrp,
            cagrp,
            layout='tabbed'
        )

        if mode != 'client':
            grps = (
                SUItem('points_programmer',
                       label='Points',
                       defined_when='mode!="client"',
                       style='custom'),

                SUItem('tray_calibration_manager',
                       label='Calibration',
                       style='custom',
                       defined_when='mode!="client"',

                ))
            cgrp.content.extend(grps)

        v = View(
            #                      VFold(agrp,
            VGroup(
                hgrp,
                pgrp,
                cgrp
            )
            #                            )
        )
        #         else:
        #             v = View()


        return v


class ControlPane(TraitsDockPane):
    name = 'Control'

    movable = False
    closable = False
    floatable = False

    def traits_view(self):
        v = View(
            VGroup(
                HGroup(
                    UItem('enabled_led',
                          editor=LEDEditor(),
                          style='custom',
                          height=-35
                    ),
                    UItem('enable', editor=ButtonEditor(label_value='enable_label'))
                ),
                HGroup(
                    Item('requested_power',
                         style='readonly',
                         format_str='%0.2f',
                         width=100
                    ),
                    Spring(springy=False, width=50),
                    UItem('units', style='readonly'),
                    spring),
                show_border=True
            ),
        )
        return v


class SupplementalPane(TraitsDockPane):
    pass

#===============================================================================
# generic
#===============================================================================
class PulsePane(TraitsDockPane):
    id = 'pychron.lasers.pulse'
    name = 'Pulse'

    def traits_view(self):
        v = View(Group(UItem('pulse', style='custom'), show_border=True))
        return v


class OpticsPane(TraitsDockPane):
    id = 'pychron.lasers.optics'
    name = 'Optics'

    def traits_view(self):
        v = View(Group(UItem('laser_controller',
                             editor=InstanceEditor(view='control_view'),
                             style='custom'),
                       show_border=True
        )
        )
        return v


class ClientPane(TraitsTaskPane):
    def traits_view(self):
        v = View(
            Item('test_connection_button', show_label=False),
            HGroup(
                UItem('enabled_led', editor=LEDEditor()),
                UItem('enable', editor=ButtonEditor(label_value='enable_label'))
            ),
            Item('position'),
            Item('x', editor=RangeEditor(low=-25.0, high=25.0)),
            Item('y', editor=RangeEditor(low=-25.0, high=25.0)),
            Item('z', editor=RangeEditor(low=-25.0, high=25.0)),
        )
        return v


class ClientDockPane(TraitsDockPane):
    name = Property(depends_on='model')
    id = 'pychron.lasers.client'

    def _get_name(self):
        n = 'Laser Client'
        if self.model:
            n = pretty_extract_device(self.model.name)
        return n

    def traits_view(self):
        pos_grp = VGroup(HGroup(Item('position'), Item('use_autocenter', label='Autocenter')),
                         Item('x', editor=RangeEditor(low=-25.0, high=25.0)),
                         Item('y', editor=RangeEditor(low=-25.0, high=25.0)),
                         Item('z', editor=RangeEditor(low=-25.0, high=25.0)),
                         label='Positioning')

        ogrp = Group(UItem('optics_client', style='custom'),
                     label='Optics')
        cgrp = Group(UItem('controls_client', style='custom'),
                     defined_when='controls_client',
                     label='Controls')

        tgrp = Group(cgrp,
                     ogrp,
                     #cgrp,
                     pos_grp, layout='tabbed')

        #add_grp = self._get_additional_grp()
        #if add_grp:
        #    pos_grp.label = 'Positioning'
        #    tgrp = Group(pos_grp, add_grp,pos_grp, layout='tabbed')
        #else:
        #    tgrp = pos_grp

        egrp = HGroup(UItem('enabled_led', editor=LEDEditor()),
                      UItem('enable', editor=ButtonEditor(label_value='enable_label')),
                      spring,
                      icon_button_editor('test_connection_button',
                                         'connect', tooltip='Test Connection'),
        )
        v = View(VGroup(egrp, tgrp))
        return v


class AuxilaryGraphPane(TraitsDockPane):
    name = 'Auxilary Graph'

    def traits_view(self):
        v = View(UItem('auxilary_graph', editor=ComponentEditor()))
        return v


# from pyface.tasks.enaml_dock_pane import EnamlDockPane
# import enaml
# class TestPane(EnamlDockPane):
#    model = Any
#    def create_component(self):
#        with enaml.imports():
#            from test_view import TestView
#
#        view = TestView(model=self.model)
#        return view
# FusionsDiodePane = BaseLaserPane

# FusionsDiodeControlPane = ControlPane
#============= EOF =============================================
