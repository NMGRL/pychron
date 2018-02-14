from __future__ import absolute_import
from pychron.lasers.stage_managers.stage_manager import StageManager

from traits.api import Float


class ChromiumStageManager(StageManager):
    xmin = Float
    xmax = Float

    ymin = Float
    ymax = Float

    zmin = Float
    zmax = Float

    y_sign = -1  # these should be config values
    x_sign = 1
    z_sign = 1

    def load(self):
        config = self.get_configuration()
        for a in ('x', 'y', 'z'):
            low, high = [float(v) for v in config.get('Axes Limits', a).split(',')]
            setattr(self, '{}min'.format(a), low)
            setattr(self, '{}max'.format(a), high)

            v = config.get('Signs', a)
            setattr(self, '{}_sign'.format(a), int(v))

        return super(ChromiumStageManager, self).load()

    def get_current_position(self):
        self.parent.update_position()
        self.debug('get_current_position {},{}'.format(self.parent.x, self.parent.y))
        return self.parent.x, self.parent.y