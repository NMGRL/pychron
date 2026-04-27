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

# ============= enthought library imports =======================
from threading import Event, current_thread, main_thread
from typing import Any as TypingAny, Callable, Optional

from traits.api import HasTraits, List, Any, Property

# ============= standard library imports ========================
# ============= local library imports  ==========================
from pychron.core.ui.gui import invoke_in_main_thread
from pychron.core.wait.wait_control import WaitControl


class WaitGroup(HasTraits):
    controls = List
    active_control = Any
    single = Property(depends_on="controls[]")

    def _get_single(self) -> bool:
        return len(self.controls) == 1

    # def traits_view(self):
    #     v = View(UItem('active_control',
    #                    style='custom',
    #                    visible_when='single',
    #                    editor=InstanceEditor()),
    #              UItem('controls',
    #                    editor=ListEditor(
    #                        use_notebook=True,
    #                        selected='active_control',
    #                        page_name='.page_name'),
    #                    style='custom',
    #                    visible_when='not single'))
    #     return v

    def _controls_default(self) -> list[WaitControl]:
        return [WaitControl()]

    def _active_control_default(self) -> WaitControl:
        return self.controls[0]

    def _invoke_on_main_thread(
        self,
        func: Callable[..., TypingAny],
        *args: TypingAny,
        wait: bool = False,
        **kw: TypingAny
    ) -> Optional[TypingAny]:
        if current_thread() is main_thread():
            return func(*args, **kw)

        if not wait:
            invoke_in_main_thread(func, *args, **kw)
            return None

        done = Event()
        result: dict[str, TypingAny] = {}

        def runner() -> None:
            try:
                result["value"] = func(*args, **kw)
            finally:
                done.set()

        invoke_in_main_thread(runner)
        done.wait()
        return result.get("value")

    def pop(self, control: Optional[WaitControl] = None) -> None:
        self._invoke_on_main_thread(self._pop, control, wait=True)

    def _pop(self, control: Optional[WaitControl] = None) -> None:
        if len(self.controls) > 1:
            if control:
                if control in self.controls:
                    self.controls.remove(control)
            else:
                self.controls.pop()

            self.active_control = self.controls[-1]

    def stop(self) -> None:
        self._invoke_on_main_thread(self._stop, wait=True)

    def _stop(self) -> None:
        for ci in self.controls:
            ci.stop()

    def ensure_control(self, control: WaitControl) -> WaitControl:
        return self._invoke_on_main_thread(self._ensure_control, control, wait=True)

    def _ensure_control(self, control: WaitControl) -> WaitControl:
        if control not in self.controls:
            self.controls.append(control)
        self.active_control = control
        return control

    def set_active_page_name(self, page_name: str) -> None:
        self._invoke_on_main_thread(self._set_active_page_name, page_name, wait=True)

    def _set_active_page_name(self, page_name: str) -> None:
        if self.active_control is not None:
            self.active_control.page_name = page_name

    def add_control(self, **kw: TypingAny) -> WaitControl:
        if "page_name" not in kw:
            kw["page_name"] = "Wait {:02d}".format(len(self.controls))
        w = WaitControl(**kw)
        self._invoke_on_main_thread(self._ensure_control, w, wait=True)
        return w

    def get_wait_control(self, **kw: TypingAny) -> WaitControl:
        return self._invoke_on_main_thread(self._get_wait_control, wait=True, **kw)

    def _get_wait_control(self, **kw: TypingAny) -> WaitControl:
        control = self.active_control
        if control is None or control.is_active():
            control = self.add_control(**kw)
        return control

    def start_wait(
        self,
        control: WaitControl,
        *,
        duration: float | None = None,
        message: str | None = None,
        paused: bool = False,
        block: bool = True,
    ) -> None:
        done = Event()
        timeout_occurred = False

        def on_finished() -> None:
            control.debug(
                "wait_group on_finished page={} status={} current_time={} thread={}".format(
                    control.page_name,
                    control.status,
                    control.current_time,
                    current_thread().name,
                )
            )
            done.set()

        control.debug(
            "wait_group start_wait page={} duration={} message={} paused={} block={} active_control={} controls={} thread={}".format(
                control.page_name,
                duration,
                message,
                paused,
                block,
                getattr(self.active_control, "page_name", None),
                len(self.controls),
                current_thread().name,
            )
        )
        self._invoke_on_main_thread(
            control.start,
            block=False,
            duration=duration,
            message=message,
            paused=paused,
            on_finished=on_finished,
            wait=True,
        )

        if block:
            control.debug(
                "wait_group waiting page={} thread={}".format(
                    control.page_name, current_thread().name
                )
            )
            # Add safety timeout to prevent indefinite hangs if Qt timer never fires
            # Timeout is duration + 5 seconds (buffer for event loop processing)
            safety_timeout = (duration or 10) + 5.0
            if not done.wait(timeout=safety_timeout):
                timeout_occurred = True
                control.warning(
                    "wait_group safety timeout triggered page={} duration={} timeout={} thread={}".format(
                        control.page_name,
                        duration,
                        safety_timeout,
                        current_thread().name,
                    )
                )
                # Force completion to prevent indefinite hang
                self._invoke_on_main_thread(control._end, wait=True)
            
            control.debug(
                "wait_group wait complete page={} status={} current_time={} timeout={} thread={}".format(
                    control.page_name,
                    control.status,
                    control.current_time,
                    timeout_occurred,
                    current_thread().name,
                )
            )


# ============= EOF =============================================
