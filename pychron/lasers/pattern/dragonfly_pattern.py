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
from traits.api import Enum
from traitsui.api import View, Item
# ============= standard library imports ========================
import time
# ============= local library imports  ==========================
from pychron.hardware.motion_controller import PositionError
from pychron.lasers.pattern.pattern_generators import line_spiral_pattern
from pychron.lasers.pattern.seek_pattern import SeekPattern


def dragonfly(st, pattern, laser_manager, controller, imgplot, cp):
    cx, cy = pattern.cx, pattern.cy

    lm = laser_manager
    sm = lm.stage_manager

    update_axes = sm.update_axes
    linear_move = controller.linear_move
    moving = sm.moving
    find_best_target = sm.find_best_target
    set_data = imgplot.data.set_data
    pr = pattern.perimeter_radius * sm.pxpermm

    def validate(xx, yy):
        return (xx ** 2 + yy ** 2) ** 0.5 <= pr

    duration = pattern.duration
    found_target = None
    while time.time() - st < pattern.total_duration:
        if found_target:
            targetxy = found_target
            found_target = None
        else:
            # identify target
            targetxy, src = find_best_target()
            set_data('imagedata', src)

        if targetxy is not None:
            tx, ty = targetxy

            if not validate(tx - cx, ty - cy):
                break
            # cp.add_point((tx - cx, ty - cy))
            try:
                linear_move(tx, ty, block=False, velocity=pattern.velocity,
                            update=False,
                            immediate=True)
            except PositionError:
                break

            time.sleep(duration)
        else:
            # do a search until a target is found
            found_target = None
            for i, (x, y) in enumerate(pattern.point_generator()):
                # cp.add_point((x, y))
                try:
                    linear_move(cx + x, cy + y, block=False, velocity=pattern.velocity,
                                update=False,
                                immediate=True)
                except PositionError:
                    break

                while moving(force_query=True):
                    update_axes()
                    found_target, src = find_best_target()
                    set_data('imagedata', src)
                    if found_target:
                        break
                    time.sleep(0.1)

                if found_target:
                    break


def outward_square_spiral(base):
    def gen():
        cnt = 0
        b = base
        py = 0
        while 1:
            if cnt == 0:
                x = px = b
                y = py
            elif cnt == 1:
                x = px
                y = py = b
            elif cnt == 2:
                x = px - b * 2
                y = py
                px = x
            elif cnt == 3:
                x = px
                y = py - b * 2
                b += 1
                cnt = -1
                py = y

            cnt += 1
            yield x, y

    return gen()


class DragonFlyPattern(SeekPattern):
    spiral_kind = Enum('Hexagon', 'Square')

    def point_generator(self):
        if self.spiral_kind == 'square':
            return outward_square_spiral(self.base)
        else:
            return line_spiral_pattern(0, 0, self.base, 200, 0.75, 6)

    def maker_view(self):
        v = View(Item('total_duration', label='Total Duration (s)',
                      tooltip='Total duration of search (in seconds)'),
                 Item('duration',
                      label='Dwell Duration (s)',
                      tooltip='Amount of time (in seconds) to wait at each point. '
                              'The brightness value is average of all measurements taken '
                              'while moving AND waiting at the vertex'),
                 Item('pre_seek_delay', label='Pre Search Delay (s)',
                      tooltip='Turn laser on and wait N seconds before starting search'),
                 Item('velocity',
                      label='Velocity (mm/s)'),
                 Item('perimeter_radius',
                      label='Perimeter Radius (mm)',
                      tooltip='Limit the search to a circular area with this radius (in mm)'),
                 Item('base',
                      label='Side (mm)',
                      tooltip="Length (in mm) of the search triangle's side"),
                 Item('saturation_threshold', label='Saturation Threshold',
                      tooltip='If the saturation score is greater than X then do not move'),
                 Item('mask_kind', label='Mask', tooltip="Define the lumen detector's mask as Hole, Beam, Custom."
                                                         "Beam= Beam radius + 10%\n"
                                                         "Hole= Hole radius"),
                 Item('custom_mask_radius', label='Mask Radius (mm)',
                      visible_when='mask_kind=="Custom"'))
        return v

# ============= EOF =============================================
