# ===============================================================================
# M3 stability diagnostics (Phase 1: instrumentation only)
#
# Adds three independent observers:
#   1. Qt message handler  -> captures "QObject::startTimer: Timers can only..."
#      style cross-thread warnings together with the originating Python stack.
#   2. QTimer thread guard -> logs (with stack) any QTimer constructed from a
#      non-main Python thread.
#   3. Main-thread watchdog -> daemon thread that records main-thread heartbeats
#      driven by a QTimer; if heartbeats stall longer than a threshold it dumps
#      every Python thread frame.  Detects "spinning beachball" wedges.
#
# Output goes to the root logger AND to a dedicated rotating file so the noisy
# diagnostic stream does not drown the experiment log.
#
# This module installs hooks only - it never alters runtime behaviour.  All
# fixes belong in Phase 2 (cross-thread marshalling).
# ===============================================================================
from __future__ import annotations

import logging
import logging.handlers
import os
import sys
import threading
import time
import traceback

_INSTALLED = False
_WATCHDOG_INSTALLED = False
_QTIMER_GUARD_INSTALLED = False
_QT_MSG_HANDLER_INSTALLED = False
_MARSHALLING_INSTALLED = False

_log = logging.getLogger("pychron.m3_diag")
_log.setLevel(logging.DEBUG)
# Do NOT propagate to root: root logger has UI/console handlers, and during
# paint-heavy code paths (icon loads, tabular paints) Qt can emit dozens of
# benign warnings (libpng iCCP, image profile, etc.) per second.  Routing
# those through the root logger stalls the main thread.  Keep diagnostic
# output in the dedicated file only.
_log.propagate = False

# Substrings that indicate a real cross-thread Qt violation.  When a Qt
# warning contains any of these we promote it to ERROR and capture the full
# Python stack.  Everything else is logged at DEBUG with no stack.
_XTHREAD_MARKERS = (
    "Timers can only be used with threads started with QThread",
    "Timers cannot be stopped from another thread",
    "Cannot create children for a parent that is in a different thread",
    "Cannot send events to objects owned by a different thread",
    "QSocketNotifier: socket notifiers cannot be enabled",
    "QSocketNotifier: Multiple socket notifiers",
    "different thread",
    "another thread",
)


def _get_log_path() -> str:
    candidates = []
    env = os.environ.get("PYCHRON_LOG_DIR")
    if env:
        candidates.append(env)
    home = os.path.expanduser("~")
    candidates.extend(
        [
            os.path.join(home, "Pychron", "logs"),
            os.path.join(home, ".pychron.0", "logs"),
            home,
        ]
    )
    for d in candidates:
        try:
            os.makedirs(d, exist_ok=True)
            test = os.path.join(d, "m3_diagnostics.log")
            # touch to verify writable
            with open(test, "a"):
                pass
            return test
        except OSError:
            continue
    return os.path.join(home, "m3_diagnostics.log")


def _attach_file_handler() -> None:
    path = _get_log_path()
    # rotate at 5 MB, keep 5 backups
    fh = logging.handlers.RotatingFileHandler(path, maxBytes=5 * 1024 * 1024, backupCount=5)
    fh.setLevel(logging.DEBUG)
    fmt = logging.Formatter("%(asctime)s %(levelname)s [%(threadName)s] %(message)s")
    fh.setFormatter(fmt)
    _log.addHandler(fh)
    _log.info("m3_diagnostics file handler attached: %s", path)


# ---------------------------------------------------------------------------
# 1. Qt message handler
# ---------------------------------------------------------------------------
def install_qt_message_handler() -> None:
    """Capture Qt warnings (esp. cross-thread timer/object misuse) with
    full Python stack and originating thread."""
    global _QT_MSG_HANDLER_INSTALLED
    if _QT_MSG_HANDLER_INSTALLED:
        return
    try:
        from pyface.qt.QtCore import qInstallMessageHandler, QtMsgType
    except Exception as e:  # pragma: no cover
        _log.error("install_qt_message_handler: import failed: %s", e)
        return

    _MODE_NAMES = {}
    for name in (
        "QtDebugMsg",
        "QtInfoMsg",
        "QtWarningMsg",
        "QtCriticalMsg",
        "QtFatalMsg",
        "QtSystemMsg",
    ):
        v = getattr(QtMsgType, name, None)
        if v is not None:
            _MODE_NAMES[int(v)] = name

    def handler(mode, ctx, msg):
        try:
            mode_name = _MODE_NAMES.get(int(mode), str(mode))
        except Exception:
            mode_name = str(mode)
        try:
            text = str(msg)
        except Exception:
            text = repr(msg)

        # Cheap path for the high-volume benign warnings: no thread lookup,
        # no stack capture, no formatting overhead beyond the log call.
        is_xthread = any(m in text for m in _XTHREAD_MARKERS)
        if not is_xthread:
            # Drop unless explicitly enabled: paint-heavy code paths can emit
            # dozens of benign Qt warnings per second (libpng iCCP, etc.) and
            # even writing them to the diag file stalls the main thread.
            if os.environ.get("PYCHRON_M3_VERBOSE_QT"):
                _log.debug("QT[%s] %s", mode_name, text)
            return

        py_thread = threading.current_thread().name
        is_main = threading.current_thread() is threading.main_thread()
        loc = ""
        for attr in ("file", "line", "function"):
            v = getattr(ctx, attr, None)
            if v:
                loc += " %s=%s" % (attr, v)
        stack = "".join(traceback.format_stack())
        _log.error(
            "QT-XTHREAD[%s] %r py_thread=%s main=%s%s\nPYTHON STACK:\n%s",
            mode_name,
            text,
            py_thread,
            is_main,
            loc,
            stack,
        )

    qInstallMessageHandler(handler)
    _QT_MSG_HANDLER_INSTALLED = True
    _log.info("Qt message handler installed")


# ---------------------------------------------------------------------------
# 2. QTimer thread guard
# ---------------------------------------------------------------------------
def install_qtimer_thread_guard() -> None:
    """Wrap QTimer.__init__ and QTimer.singleShot so any non-main-thread use
    is logged with stack."""
    global _QTIMER_GUARD_INSTALLED
    if _QTIMER_GUARD_INSTALLED:
        return
    try:
        from pyface.qt.QtCore import QTimer
    except Exception as e:  # pragma: no cover
        _log.error("install_qtimer_thread_guard: import failed: %s", e)
        return

    orig_init = QTimer.__init__
    orig_single_shot = QTimer.singleShot

    def init_wrapper(self, *args, **kwargs):
        if threading.current_thread() is not threading.main_thread():
            _log.error(
                "QTimer() constructed off main thread (thread=%s)\n%s",
                threading.current_thread().name,
                "".join(traceback.format_stack()),
            )
        return orig_init(self, *args, **kwargs)

    def single_shot_wrapper(*args, **kwargs):
        if threading.current_thread() is not threading.main_thread():
            _log.error(
                "QTimer.singleShot called off main thread (thread=%s)\n%s",
                threading.current_thread().name,
                "".join(traceback.format_stack()),
            )
        return orig_single_shot(*args, **kwargs)

    try:
        QTimer.__init__ = init_wrapper
        QTimer.singleShot = single_shot_wrapper
        _QTIMER_GUARD_INSTALLED = True
        _log.info("QTimer thread guard installed")
    except (TypeError, AttributeError) as e:
        # PyQt/PySide may forbid replacing C++ slot wrappers.  Fall back to
        # a __init_subclass__-style check by hooking the metaclass would be
        # overkill; just log and continue - Qt message handler will still
        # catch the underlying startTimer warnings.
        _log.warning("QTimer thread guard could not be installed: %s", e)


# ---------------------------------------------------------------------------
# 3. Main-thread watchdog
# ---------------------------------------------------------------------------
class _Watchdog:
    def __init__(
        self, stall_threshold: float = 2.0, dump_cooldown: float = 10.0, heartbeat_ms: int = 500
    ):
        self.stall_threshold = stall_threshold
        self.dump_cooldown = dump_cooldown
        self.heartbeat_ms = heartbeat_ms
        self.last_heartbeat = time.monotonic()
        self.last_dump = 0.0
        self.timer = None
        self._poll_thread = None

    def _on_heartbeat(self):
        self.last_heartbeat = time.monotonic()

    def _poll(self):
        # rate: 4x per second
        while True:
            time.sleep(0.25)
            now = time.monotonic()
            gap = now - self.last_heartbeat
            if gap >= self.stall_threshold and (now - self.last_dump) >= self.dump_cooldown:
                self.last_dump = now
                self._dump(gap)

    def _dump(self, gap: float):
        try:
            frames = sys._current_frames()
            lines = ["MAIN-THREAD STALL %.2fs (threshold %.2fs)" % (gap, self.stall_threshold)]
            # Map thread ids -> Thread objects for names
            by_id = {t.ident: t for t in threading.enumerate()}
            for tid, frame in frames.items():
                t = by_id.get(tid)
                tname = t.name if t else "tid=%s" % tid
                is_main = bool(t and t is threading.main_thread())
                lines.append("---- Thread %s%s ----" % (tname, " (MAIN)" if is_main else ""))
                lines.extend(traceback.format_stack(frame))
            _log.error("\n".join(lines))
        except Exception as e:  # pragma: no cover
            _log.exception("watchdog dump failed: %s", e)

    def start_main_timer(self):
        # called from main thread once QApplication exists
        try:
            from pyface.qt.QtCore import QTimer
        except Exception as e:  # pragma: no cover
            _log.error("watchdog: QTimer import failed: %s", e)
            return
        self.timer = QTimer()
        self.timer.setInterval(self.heartbeat_ms)
        self.timer.timeout.connect(self._on_heartbeat)
        self.timer.start()
        _log.info("watchdog: main-thread heartbeat QTimer started (%d ms)", self.heartbeat_ms)

    def start_poll_thread(self):
        self._poll_thread = threading.Thread(target=self._poll, name="M3Watchdog", daemon=True)
        self._poll_thread.start()
        _log.info(
            "watchdog: poll thread started (stall=%.1fs, cooldown=%.1fs)",
            self.stall_threshold,
            self.dump_cooldown,
        )


_watchdog: _Watchdog | None = None


# ---------------------------------------------------------------------------
# 4. Phase 2 cross-thread marshalling
#
# Worker threads (run threads, _do_collection, etc.) frequently end up
# scheduling Qt timers via pyface helpers such as do_after_timer.  On macOS
# ARM64 these timers are bound to whichever Qt thread context happened to
# be active when they were started; once the worker thread exits, the
# QObject's parent context is gone and the next time the timer fires Qt
# dereferences a stale pointer, which on M3 triggers a PAC fault and
# SIGBUS/SIGSEGV.  Intel silently dereferences the garbage and limps on,
# Apple Silicon does not.
#
# The fix is to force every Qt-timer scheduling helper to run on the main
# thread.  We patch the three documented entry points used by pychron and
# its dependencies.  Caller behaviour is preserved when already on the
# main thread; when called off-main, the scheduling is deferred to the
# main thread via pychron.core.ui.gui.invoke_in_main_thread (which
# ultimately uses GUI.invoke_later -> Qt queued connection).  The
# *callable* the caller passed to do_after_timer still runs on the main
# thread, so any UI code it touches is now thread-correct.
# ---------------------------------------------------------------------------
def _on_main_thread() -> bool:
    return threading.current_thread() is threading.main_thread()


def _marshal(fn, *args, **kwargs):
    """Run fn on the main thread (deferred).  Returns None synchronously."""
    from pychron.core.ui.gui import invoke_in_main_thread

    invoke_in_main_thread(fn, *args, **kwargs)
    return None


def install_thread_safe_marshalling() -> None:
    """Patch pyface timer entry points so off-main-thread callers no longer
    create QTimers bound to dying worker thread contexts."""
    global _MARSHALLING_INSTALLED
    if _MARSHALLING_INSTALLED:
        return

    patched = []

    # --- pyface.timer.do_later.do_after / do_later ----------------------------
    try:
        import pyface.timer.do_later as _dl

        if hasattr(_dl, "do_after"):
            _orig_do_after = _dl.do_after

            def _safe_do_after(ms, callable_, *a, **kw):
                if _on_main_thread():
                    return _orig_do_after(ms, callable_, *a, **kw)
                _log.debug(
                    "marshalling do_after from %s",
                    threading.current_thread().name,
                )
                return _marshal(_orig_do_after, ms, callable_, *a, **kw)

            _dl.do_after = _safe_do_after
            patched.append("pyface.timer.do_later.do_after")

        if hasattr(_dl, "do_later"):
            _orig_do_later = _dl.do_later

            def _safe_do_later(callable_, *a, **kw):
                if _on_main_thread():
                    return _orig_do_later(callable_, *a, **kw)
                _log.debug(
                    "marshalling do_later from %s",
                    threading.current_thread().name,
                )
                return _marshal(_orig_do_later, callable_, *a, **kw)

            _dl.do_later = _safe_do_later
            patched.append("pyface.timer.do_later.do_later")
    except Exception as e:  # pragma: no cover
        _log.error("marshalling: pyface.timer.do_later patch failed: %s", e)

    # --- pyface.timer.i_timer.CallbackTimer.single_shot -----------------------
    # do_after_timer routes through CallbackTimer.single_shot, but other
    # call sites (e.g. ITimer.single_shot used by traitsui editors) also do.
    # Patch the classmethod on the implementation class to catch every path.
    try:
        from pyface.timer.timer import CallbackTimer as _CBT

        _orig_single_shot = _CBT.single_shot

        def _safe_single_shot(cls, *a, **kw):
            if _on_main_thread():
                return _orig_single_shot.__func__(cls, *a, **kw)
            _log.debug(
                "marshalling CallbackTimer.single_shot from %s",
                threading.current_thread().name,
            )
            return _marshal(_orig_single_shot.__func__, cls, *a, **kw)

        _CBT.single_shot = classmethod(_safe_single_shot)
        patched.append("pyface.timer.i_timer.CallbackTimer.single_shot")
    except Exception as e:  # pragma: no cover
        _log.error("marshalling: CallbackTimer.single_shot patch failed: %s", e)

    # --- pyface.qt.QtCore.QTimer.singleShot ----------------------------------
    # Lowest level: any direct PyQt/PySide QTimer.singleShot call from a
    # worker thread.  The earlier Phase 1 guard only logged; now marshal.
    try:
        from pyface.qt.QtCore import QTimer

        _orig_qt_single_shot = QTimer.singleShot

        def _safe_qt_single_shot(*a, **kw):
            if _on_main_thread():
                return _orig_qt_single_shot(*a, **kw)
            _log.debug(
                "marshalling QTimer.singleShot from %s",
                threading.current_thread().name,
            )
            return _marshal(_orig_qt_single_shot, *a, **kw)

        try:
            QTimer.singleShot = _safe_qt_single_shot
            patched.append("pyface.qt.QtCore.QTimer.singleShot")
        except (TypeError, AttributeError) as e:
            _log.warning(
                "marshalling: QTimer.singleShot replacement rejected by " "PyQt/PySide binding: %s",
                e,
            )
    except Exception as e:  # pragma: no cover
        _log.error("marshalling: QTimer.singleShot patch failed: %s", e)

    _MARSHALLING_INSTALLED = True
    _log.info("thread-safe marshalling installed: %s", ", ".join(patched))


_EVENT_TRACER_INSTALLED = False
_event_tracer = None  # keep a strong ref so Qt doesn't GC the filter


def install_event_tracer() -> None:
    """Install a QApplication-level event filter that logs every Qt Timer
    event delivery to a dedicated rotating file (m3_eventtrace.log).

    Each line: timestamp + receiver class name + receiver Python id +
    timer_id (where exposed by the binding).  When the process segfaults
    inside QCoreApplication::notifyInternal2, the last few lines of this
    file identify which receiver class was about to be dispatched to.

    Volume control: only Timer events are traced (Qt event type 1).  The
    full event stream is far too noisy to dump per delivery.
    """
    global _EVENT_TRACER_INSTALLED, _event_tracer
    if _EVENT_TRACER_INSTALLED:
        return
    try:
        from pyface.qt.QtCore import QObject, QEvent, QCoreApplication
    except Exception as e:  # pragma: no cover
        _log.error("install_event_tracer: import failed: %s", e)
        return

    app = QCoreApplication.instance()
    if app is None:
        _log.error("install_event_tracer: no QApplication instance; call after app_factory")
        return

    # Dedicated logger + rotating file so the trace volume does not pollute
    # the main diagnostics log.  Unbuffered (flush per line) so the most
    # recent receivers survive a SIGSEGV.
    trace_logger = logging.getLogger("pychron.m3_diag.eventtrace")
    trace_logger.setLevel(logging.DEBUG)
    trace_logger.propagate = False
    if not trace_logger.handlers:
        trace_path = os.path.join(os.path.dirname(_get_log_path()), "m3_eventtrace.log")
        try:
            fh = logging.handlers.RotatingFileHandler(
                trace_path, maxBytes=5 * 1024 * 1024, backupCount=3
            )
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(
                logging.Formatter("%(asctime)s.%(msecs)03d %(message)s", datefmt="%H:%M:%S")
            )
            trace_logger.addHandler(fh)
        except OSError as e:
            _log.error("install_event_tracer: log open failed: %s", e)
            return

    TIMER_EVT = int(QEvent.Timer)

    class _EventTracer(QObject):
        def eventFilter(self, obj, ev):
            try:
                if int(ev.type()) == TIMER_EVT:
                    try:
                        tid = ev.timerId()
                    except Exception:
                        tid = -1
                    # Capture receiver class + id() BEFORE Qt dispatches.
                    # If receiver is already dangling, accessing type(obj)
                    # may itself fault - but a faulting trace point still
                    # tells us we got here, and a successful one identifies
                    # the next dispatch target.
                    trace_logger.debug(
                        "Timer cls=%s pyid=0x%x qtid=%d",
                        type(obj).__name__,
                        id(obj),
                        tid,
                    )
            except Exception:
                # Tracing must never interfere with event delivery; a
                # dangling receiver may itself fault on type() lookup
                # here and that's expected (the unfinished trace line
                # already tells us a bad receiver is in flight).
                pass
            return False  # never consume

    _event_tracer = _EventTracer()
    try:
        app.installEventFilter(_event_tracer)
    except Exception as e:
        _log.error("install_event_tracer: installEventFilter failed: %s", e)
        return

    _EVENT_TRACER_INSTALLED = True
    _log.info("event tracer installed (Timer events -> m3_eventtrace.log)")


def install_main_thread_watchdog(stall_threshold: float = 2.0) -> None:
    """Start the watchdog poll thread immediately and arm the main-thread
    QTimer.  Must be called from the main thread, after the QApplication has
    been constructed but before its event loop is exec'd."""
    global _watchdog, _WATCHDOG_INSTALLED
    if _WATCHDOG_INSTALLED:
        return
    _watchdog = _Watchdog(stall_threshold=stall_threshold)
    _watchdog.start_main_timer()
    _watchdog.start_poll_thread()
    _WATCHDOG_INSTALLED = True


# ---------------------------------------------------------------------------
# top-level entry points
# ---------------------------------------------------------------------------
def install_early() -> None:
    """Install everything that does not need a running QApplication.
    Call as early as possible (before any Qt object is constructed)."""
    global _INSTALLED
    if _INSTALLED:
        return
    _attach_file_handler()
    install_qt_message_handler()
    install_qtimer_thread_guard()
    _INSTALLED = True
    _log.info("m3_diagnostics: early install complete (pid=%d)", os.getpid())


def install_late(stall_threshold: float = 5.0) -> None:
    """Install hooks that require a constructed QApplication.  Call right
    after app_factory() and before app.run().

    Phase 2 marshalling is also installed here (technically it does not
    require a running QApplication, but it does require pyface to be fully
    imported, which is only guaranteed once app_factory has run)."""
    install_thread_safe_marshalling()
    install_main_thread_watchdog(stall_threshold=stall_threshold)
    # Event tracer is opt-in: it logs one line per Timer event delivered
    # on the main thread, which is verbose.  Enable when hunting a crash
    # inside QCoreApplication::notifyInternal2 by setting
    # PYCHRON_M3_EVENT_TRACE=1 in the environment.
    if os.environ.get("PYCHRON_M3_EVENT_TRACE"):
        install_event_tracer()


# ============= EOF =============================================
