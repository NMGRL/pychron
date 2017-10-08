
from gp_actuator import GPActuator


class DummyGPActuator(GPActuator):

    def __init__(self, *args, **kw):
        super(DummyGPActuator, self).__init__(*args, **kw)
        self._states = {}

    def open_channel(self, ch, *args, **kw):
        self._states[ch] = True
        return True

    def close_channel(self, ch, *args, **kw):
        self._states[ch] = False
        return True

    def get_channel_state(self, ch, *args, **kw):
        return self._states.get(ch, False)

    def get_state_checksum(self, *args, **kw):
        return 0

    def get_open_indicator_state(self, *args, **kw):
        """
        """
        return self.get_channel_state(*args, **kw)

    def get_closed_indicator_state(self, *args, **kw):
        """
        """
        return not self.get_channel_state(*args, **kw)