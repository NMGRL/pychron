# ===============================================================================
# Copyright 2013 Jake Ross
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

# ============= standard library imports ========================
from threading import current_thread, Timer
from typing import Any, Callable

# ============= enthought library imports =======================
from pyface.qt.QtCore import QTimer
from pyface.qt.QtWidgets import QApplication
from traits.api import Str, Button, Float, Bool, Property, Int, Event as TEvent
from pyface.ui_traits import PyfaceColor

# ============= local library imports  ==========================
from pychron.core.helpers.ctx_managers import no_update
from pychron.loggable import Loggable


class WaitControl(Loggable):
    page_name = Str("Wait")
    message = Str("")
    message_color = PyfaceColor("black")
    message_bgcolor = PyfaceColor("#eaebbc")

    high = Int(auto_set=False, enter_set=True)
    duration = Float(10)

    current_time = Float
    current_display_time = Property(depends_on="current_time")

    auto_start = Bool(False)
    timer = None
    _backup_timer: Timer | None = None
    _on_finished: Callable[[], None] | None = None

    continue_button = Button("Continue")
    pause_button = TEvent
    pause_label = Property(depends_on="_paused")
    status = Str("idle")
    _paused = Bool
    _continued = Bool
    _canceled = Bool
    _no_update = False

    def __init__(self, *args: Any, **kw: Any) -> None:
        self.reset()
        super(WaitControl, self).__init__(*args, **kw)
        if self.auto_start:
            self.start(block=False)

    def _get_timer(self) -> QTimer:
        timer = self.timer
        if timer is None:
            app = QApplication.instance()
            timer = QTimer(app) if app is not None else QTimer()
            timer.setInterval(1000)
            timer.timeout.connect(self._update_time)
            self.timer = timer
            self.debug(
                "wait_control timer created page={} timer_id={} app_present={} thread={}".format(
                    self.page_name,
                    id(timer),
                    app is not None,
                    current_thread().name,
                )
            )
        return timer

    def _start_timer(self) -> None:
        timer = self._get_timer()
        if timer.isActive():
            timer.stop()
            # Disconnect signal if timer is being reused
            try:
                timer.timeout.disconnect()
            except (RuntimeError, AttributeError, TypeError):
                pass
            self.debug(
                "wait_control timer restarted page={} timer_id={} current_time={} status={} thread={}".format(
                    self.page_name,
                    id(timer),
                    self.current_time,
                    self.status,
                    current_thread().name,
                )
            )
        else:
            self.debug(
                "wait_control timer starting page={} timer_id={} current_time={} status={} thread={}".format(
                    self.page_name,
                    id(timer),
                    self.current_time,
                    self.status,
                    current_thread().name,
                )
            )
        
        # Reconnect signal to ensure clean state
        try:
            timer.timeout.disconnect()
        except (RuntimeError, AttributeError, TypeError):
            pass
        timer.timeout.connect(self._update_time)
        timer.start()
        
        # Start backup threading timer as safety net in case Qt timer never fires
        # (can happen if main thread event loop is blocked)
        self._stop_backup_timer()
        backup_duration = max(self.duration + 2.0, 3.0)  # Add 2s buffer, minimum 3s
        self._backup_timer = Timer(backup_duration, self._backup_timer_fired)
        self._backup_timer.daemon = True
        self._backup_timer.start()
        self.debug(
            "wait_control backup timer started page={} duration={} thread={}".format(
                self.page_name, backup_duration, current_thread().name
            )
        )

    def _stop_backup_timer(self) -> None:
        """Cancel the backup threading timer"""
        if self._backup_timer is not None:
            if self._backup_timer.is_alive():
                self._backup_timer.cancel()
            self._backup_timer = None

    def _backup_timer_fired(self) -> None:
        """Backup timer fired - force completion if on_finished not already called"""
        if self._on_finished is not None:
            self.warning(
                "wait_control backup timer triggered - Qt timer may be hung page={} status={} current_time={} thread={}".format(
                    self.page_name,
                    self.status,
                    self.current_time,
                    current_thread().name,
                )
            )
            # Force end to trigger on_finished callback
            self._end()

    def _stop_timer(self) -> None:
        timer = self.timer
        if timer is not None and timer.isActive():
            self.debug(
                "wait_control timer stopping page={} timer_id={} current_time={} status={} thread={}".format(
                    self.page_name,
                    id(timer),
                    self.current_time,
                    self.status,
                    current_thread().name,
                )
            )
            try:
                timer.stop()
                timer.timeout.disconnect()
            except (RuntimeError, AttributeError, TypeError):
                pass
        
        # Also stop backup timer
        self._stop_backup_timer()

    def is_active(self) -> bool:
        return bool(self.timer and self.timer.isActive())

    def _is_timer_active(self) -> bool:
        return self.is_active()

    def is_canceled(self) -> bool:
        return self.status in ("canceled", "stopped")

    def is_continued(self) -> bool:
        return self.status == "continued"

    def set_message(
        self,
        message: str,
        *,
        color: str | None = None,
        bgcolor: str | None = None,
        wait: bool = True,
    ) -> None:
        traits: dict[str, Any] = {"message": message}
        if color is not None:
            traits["message_color"] = color
        if bgcolor is not None:
            traits["message_bgcolor"] = bgcolor
        self.trait_set(**traits)

    def set_remaining_time(self, remaining: float, *, wait: bool = False) -> None:
        self.trait_set(current_time=remaining)

    def continue_wait(self) -> None:
        self._continue()

    def _finish(
        self,
        status: str,
        *,
        remaining_time: float | None = None,
        message: str | None = None,
        color: str | None = None,
    ) -> None:
        traits: dict[str, Any] = {
            "status": status,
            "_continued": status == "continued",
            "_canceled": status in ("canceled", "stopped"),
        }
        if remaining_time is not None:
            traits["current_time"] = remaining_time
        if message is not None:
            traits["message"] = message
        if color is not None:
            traits["message_color"] = color

        self.debug(
            "wait_control finish page={} from_status={} to_status={} remaining_time={} message={} thread={}".format(
                self.page_name,
                self.status,
                status,
                remaining_time,
                message,
                current_thread().name,
            )
        )
        self.trait_set(**traits)

        self._stop_timer()
        on_finished = self._on_finished
        self._on_finished = None
        if on_finished is not None:
            on_finished()

    def start(
        self,
        block: bool = True,
        duration: float | None = None,
        message: str | None = None,
        paused: bool = False,
        on_finished: Callable[[], None] | None = None,
    ) -> None:
        if block:
            raise RuntimeError(
                "WaitControl.start(block=True) is no longer supported; "
                "start waits via WaitGroup.start_wait or a caller-owned completion event"
            )

        self.debug(
            "wait_control start page={} duration_arg={} message={} paused={} current_time={} status={} thread={}".format(
                self.page_name,
                duration,
                message,
                paused,
                self.current_time,
                self.status,
                current_thread().name,
            )
        )
        self._on_finished = on_finished
        self._stop_timer()

        if duration is not None:
            self.duration = duration
            self.reset()

        if message:
            self.set_message(message)

        self._start_timer()
        self.trait_set(
            status="running",
            _continued=False,
            _canceled=False,
            _paused=paused,
            message_color="black",
            message_bgcolor="#eaebbc",
        )

    def stop(self) -> None:
        status = "stopped" if self.is_active() else "canceled"
        self.debug(
            "wait_control stop page={} chosen_status={} current_time={} status={} thread={}".format(
                self.page_name,
                status,
                self.current_time,
                self.status,
                current_thread().name,
            )
        )
        self._finish(status)
        self.debug("wait dialog stopped")
        if self.current_time > 1:
            self.set_message("Stopped", color="red")

    def reset(self) -> None:
        with no_update(self, fire_update_needed=False):
            self.trait_set(
                high=int(self.duration),
                current_time=self.duration,
                status="idle",
                _paused=False,
                _continued=False,
                _canceled=False,
            )

    def pause(self) -> None:
        self.trait_set(_paused=True)

    # ===============================================================================
    # private
    # ===============================================================================

    def _continue(self) -> None:
        self.debug(
            "wait_control continue page={} current_time={} status={} thread={}".format(
                self.page_name, self.current_time, self.status, current_thread().name
            )
        )
        self.trait_set(_paused=False)
        self._finish("continued", remaining_time=0, message="")

    def _end(self) -> None:
        self.debug(
            "wait_control end page={} current_time={} status={} thread={}".format(
                self.page_name, self.current_time, self.status, current_thread().name
            )
        )
        self._finish("completed", remaining_time=0, message="")

    def _update_time(self) -> None:
        try:
            if self._paused:
                self.debug(
                    "wait_control tick skipped page={} current_time={} status={} paused={} thread={}".format(
                        self.page_name,
                        self.current_time,
                        self.status,
                        self._paused,
                        current_thread().name,
                    )
                )
                return
            ct = self.current_time
            if self._is_timer_active():
                ct -= 1
                self.debug(
                    "wait_control tick page={} next_time={} current_time={} status={} thread={}".format(
                        self.page_name,
                        ct,
                        self.current_time,
                        self.status,
                        current_thread().name,
                    )
                )
                # self.debug('Current Time={}/{}'.format(ct, self.duration))
                if ct <= 0:
                    self._end()
                else:
                    self.set_remaining_time(ct)
        except (RuntimeError, AttributeError, ReferenceError):
            # Object was deleted or is being cleaned up
            pass

                # def _current_time_changed(self):
                # if self.current_time <= 0:
                # self._end()
                # self._canceled = False

    def _get_current_display_time(self) -> str:
        return "{:03d}".format(int(self.current_time))

    def _get_pause_label(self) -> str:
        return "Unpause" if self._paused else "Pause"

    # ===============================================================================
    # handlers
    # ===============================================================================
    def _pause_button_fired(self) -> None:
        self.trait_set(_paused=not self._paused)

    def _continue_button_fired(self) -> None:
        self.continue_wait()

    def _high_changed(self, v: int) -> None:
        if self._no_update:
            return

        self.duration = v
        self.set_remaining_time(v)

        # def traits_view(self):
        # v = View(VGroup(
        #         CustomLabel('message',
        #                     size=14,
        #                     weight='bold',
        #                     color_name='message_color'),
        #
        #         HGroup(Spring(width=-5, springy=False),
        #                Item('high', label='Set Max. Seconds'),
        #                spring, UItem('continue_button')),
        #         HGroup(Spring(width=-5, springy=False),
        #                Item('current_time', show_label=False,
        #                     editor=RangeEditor(mode='slider',
        #                                        low=1,
        #                                        # low_name='low_name',
        #                                        high_name='duration')),
        #                CustomLabel('current_time',
        #                            size=14,
        #                            weight='bold'))))
        #     return v


# ============= EOF =============================================
