from actuator import Actuator


class DummyController(Actuator):

    def get_state_checksum(self, *args, **kw):
        if self._cdevice:
            return self._cdevice.get_state_checksum(*args, **kw)

    def get_open_indicator_state(self, *args, **kw):
        """
        """
        if self._cdevice is not None:
            return self._cdevice.get_open_indicator_state(*args, **kw)

    def get_closed_indicator_state(self, *args, **kw):
        """
        """
        if self._cdevice is not None:
            return self._cdevice.get_close_indicator_state(*args, **kw)