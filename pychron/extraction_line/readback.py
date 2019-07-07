# from datetime import datetime
#
# from pychron.hardware.core.core_device import CoreDevice
# from pychron.loggable import Loggable
# from traits.api import HasTraits, Str, Any, Property, List, Event
# from traitsui.api import View, UItem, Item
#
# from pychron.pychron_constants import NULL_STR
#
#
# class ReadbackItem(HasTraits):
#     name = Str
#     # readback_display = Property(depends_on='readback_value')
#     value = Str
#     command = Str
#     # fmt = Str
#     invalid_value = NULL_STR
#     timestamp = Str
#     _last_timestamp = None
#     refresh_needed = Event
#
#     def __init__(self, dev, *args, **kw):
#         super(ReadbackItem, self).__init__(*args, **kw)
#         self.name = dev.name
#         dev.setup_response_readback(self._handle)
#
#     def _handle(self, new):
#         now = datetime.now()
#         fmt = '%H:%M:%S'
#         if self._last_timestamp:
#             if now.day != self._last_timestamp.day:
#                 fmt = '%m/%d %H:%M:%S'
#
#         self.timestamp = now.strftime(fmt)
#         self._last_timestamp = now
#
#         if new:
#             self.value = str(new.get('value'))
#             self.command = new.get('command')
#
#             # self.refresh_needed = True
