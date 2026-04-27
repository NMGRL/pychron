# ===============================================================================
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
# ===============================================================================

# ============= enthought library imports =======================
from __future__ import absolute_import
from pychron.core.ui.factory import toolkit_factory


# ============= standard library imports ========================
import time
import threading
from functools import wraps
# ============= local library imports  ==========================

# invoke_in_main_thread = toolkit_factory('gui', 'invoke_in_main_thread')

from pychron.core.helpers.logger_setup import new_logger

logger = new_logger("EventLoopMonitor")

# Event loop health monitoring
_event_loop_last_check = None
_event_loop_warning_threshold = 1.0  # seconds - warn if event loop unresponsive for this long
_monitoring_enabled = True


def set_event_loop_warning_threshold(seconds):
    """Set the warning threshold for event loop responsiveness (in seconds)."""
    global _event_loop_warning_threshold
    _event_loop_warning_threshold = seconds
    logger.debug(f"Event loop warning threshold set to {seconds}s")


def invoke_in_main_thread(fn, *args, **kw):
    """Invoke function in main Qt thread with instrumentation.
    
    Tracks execution timing and logs warnings if the main thread
    is unresponsive (blocked) for significant periods.
    """
    from pyface.gui import GUI
    
    # Record timing of callback invocation
    _invocation_time = time.time()
    
    def _instrumented_fn(*args, **kw):
        elapsed = time.time() - _invocation_time
        fn_name = getattr(fn, '__name__', str(fn))
        
        if elapsed > _event_loop_warning_threshold:
            logger.warning(
                f"Event loop was blocked for {elapsed:.2f}s before invoking {fn_name}. "
                "This may indicate the main thread is stalled."
            )
        
        try:
            return fn(*args, **kw)
        except Exception as e:
            logger.exception(f"Exception in invoke_in_main_thread callback {fn_name}: {e}")
            raise
    
    GUI.invoke_later(_instrumented_fn, *args, **kw)


def time_operation(threshold=1.0):
    """Decorator to track operation timing and warn if execution is slow.
    
    Args:
        threshold: Time in seconds - warn if operation exceeds this
        
    Usage:
        @time_operation(threshold=2.0)
        def long_running_operation():
            ...
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kw):
            fn_name = fn.__name__
            start = time.time()
            
            try:
                result = fn(*args, **kw)
                elapsed = time.time() - start
                
                if elapsed > threshold:
                    logger.warning(
                        f"Slow operation: {fn_name} took {elapsed:.2f}s "
                        f"(threshold: {threshold}s)"
                    )
                else:
                    logger.debug(f"{fn_name} completed in {elapsed:.3f}s")
                
                return result
            except Exception as e:
                elapsed = time.time() - start
                logger.exception(
                    f"Exception in {fn_name} after {elapsed:.2f}s: {e}"
                )
                raise
        
        return wrapper
    return decorator


def assert_main_thread(fn_name=""):
    """Assert that code is running on the main Qt thread.
    
    Args:
        fn_name: Name of function for logging purposes
        
    Raises:
        RuntimeError if not on main thread
    """
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QThread
    
    main_thread = QApplication.instance().thread()
    current_thread = QThread.currentThread()
    
    if main_thread != current_thread:
        logger.error(
            f"{fn_name} called from worker thread! "
            f"Qt operations must run on main thread. "
            f"Use invoke_in_main_thread() to defer to main thread."
        )
        raise RuntimeError(
            f"Qt operation called from non-main thread in {fn_name}"
        )


def check_event_loop_health():
    """Check if main Qt event loop is responsive.
    
    Posts a health check event to the main thread and measures
    how long it takes to execute. Returns timing metrics.
    
    Returns:
        dict: {'responsive': bool, 'delay_ms': float, 'timestamp': float}
    """
    if not _monitoring_enabled:
        return {'responsive': True, 'delay_ms': 0, 'timestamp': time.time()}
    
    from pyface.gui import GUI
    
    check_start = time.time()
    result = {'responsive': False, 'delay_ms': 0, 'timestamp': check_start}
    
    def _health_check():
        elapsed_ms = (time.time() - check_start) * 1000
        result['delay_ms'] = elapsed_ms
        result['responsive'] = elapsed_ms < _event_loop_warning_threshold * 1000
        
        if not result['responsive']:
            logger.warning(
                f"Event loop health check: unresponsive "
                f"(delay: {elapsed_ms:.1f}ms, threshold: {_event_loop_warning_threshold*1000:.1f}ms)"
            )
    
    try:
        GUI.invoke_later(_health_check)
        return result
    except Exception as e:
        logger.exception(f"Error checking event loop health: {e}")
        return {'responsive': False, 'delay_ms': -1, 'timestamp': check_start}


def enable_event_loop_monitoring(enabled=True):
    """Enable/disable event loop monitoring.
    
    When enabled, tracks main thread responsiveness and logs warnings
    for slow operations and unresponsive event loops.
    """
    global _monitoring_enabled
    _monitoring_enabled = enabled
    status = "enabled" if enabled else "disabled"
    logger.info(f"Event loop monitoring {status}")


convert_color = toolkit_factory("gui", "convert_color")
wake_screen = toolkit_factory("gui", "wake_screen")
# ============= EOF =============================================
