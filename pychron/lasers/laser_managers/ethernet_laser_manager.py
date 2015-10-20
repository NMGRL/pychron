from traits.api import Float, Property, Bool, Button, String, Enum
from pychron.core.ui.thread import Thread
from pychron.globals import globalv
from pychron.hardware.pychron_device import EthernetDeviceMixin
from pychron.lasers.laser_managers.base_lase_manager import BaseLaserManager


class EthernetLaserManager(BaseLaserManager, EthernetDeviceMixin):
    position = String(enter_set=True, auto_set=False)
    x = Property(depends_on='_x')
    y = Property(depends_on='_y')
    z = Property(depends_on='_z')
    _x = Float
    _y = Float
    _z = Float
    connected = Bool
    test_connection_button = Button('Test Connection')
    snapshot_button = Button('Test Snapshot')
    use_autocenter = Bool(False)

    output_power = Float(enter_set=True, auto_set=False)
    fire_laser_button = Button('Fire')
    units = Enum('watts', 'percent')

    _patterning = False
    _firing = False

    stage_stop_button = Button('Stage Stop')
    move_enabled_button = Button('Enable Move')
    _move_enabled = False

    def open(self, *args, **kw):
        return EthernetDeviceMixin.open(self)

    def opened(self):
        self.debug('opened')
        if self.update_position():
            self._opened_hook()
            return True

    def update_position(self):
        pos = super(EthernetLaserManager, self).update_position()
        if pos:
            self.trait_set(**dict(zip(('_x', '_y', '_z'), pos)))
            return True

    # private
    def _test_connection_button_fired(self):
        self.test_connection()
        if self.connected:
            self.opened()

    def _test_connection(self):
        if self.simulation:
            return globalv.communication_simulation
        else:
            if self.setup_communicator():
                self.debug('test connection. connected= {}'.format(self.connected))
            return self.connected

    def _position_changed(self):
        if self.position is not None:
            t = Thread(target=self._move_to_position,
                       args=(self.position, self.use_autocenter))
            t.start()
            self._position_thread = t

    def _enable_fired(self):
        if self.enabled:
            self.disable_laser()
            self.enabled = False
        else:
            if self.enable_laser():
                self.enabled = True

    def _move_enabled_button_fired(self):
        self._move_enabled = not self._move_enabled

    def _opened_hook(self):
        pass

    def _get_x(self):
        return self._x

    def _get_y(self):
        return self._y

    def _get_z(self):
        return self._z