from __future__ import absolute_import

import os
import subprocess
import sys
import textwrap
from typing import Optional

from pyface.splash_screen import SplashScreen

from pychron.core.helpers.logger_setup import new_logger

logger = new_logger("GIFSplashScreen")

_SPLASH_PROCESS_SCRIPT = textwrap.dedent(
    """
    import os
    import sys

    def _import_qt():
        for api in ("PyQt5", "PySide6", "PySide2"):
            try:
                if api == "PyQt5":
                    from PyQt5 import QtCore, QtGui, QtWidgets
                elif api == "PySide6":
                    from PySide6 import QtCore, QtGui, QtWidgets
                else:
                    from PySide2 import QtCore, QtGui, QtWidgets
                return QtCore, QtGui, QtWidgets
            except Exception:
                continue
        raise RuntimeError("No supported Qt binding found for GIF splash")

    def _center(widget, app, qt_widgets):
        geometry = None
        if hasattr(app, "primaryScreen"):
            screen = app.primaryScreen()
            if screen is not None:
                geometry = screen.availableGeometry()
        if geometry is None and hasattr(app, "desktop"):
            desktop = app.desktop()
            if desktop is not None:
                geometry = desktop.screenGeometry()
        if geometry is not None:
            widget.move(geometry.center() - widget.rect().center())

    def main():
        gif_path = sys.argv[1]
        QtCore, QtGui, QtWidgets = _import_qt()

        app = QtWidgets.QApplication(sys.argv)
        flags = (
            QtCore.Qt.SplashScreen
            | QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.WindowStaysOnTopHint
        )
        widget = QtWidgets.QLabel(None, flags)
        widget.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        widget.setAlignment(QtCore.Qt.AlignCenter)

        movie = QtGui.QMovie(gif_path)
        movie.frameChanged.connect(lambda _i: _center(widget, app, QtWidgets))
        widget.setMovie(movie)
        movie.start()

        pixmap = movie.currentPixmap()
        if not pixmap.isNull():
            widget.resize(pixmap.size())
        _center(widget, app, QtWidgets)
        widget.show()

        sys.exit(app.exec_() if hasattr(app, "exec_") else app.exec())

    if __name__ == "__main__":
        main()
    """
)


class GIFSplashScreen(SplashScreen):
    def __init__(self, image_path: str, **traits):
        traits.setdefault("show_log_messages", False)
        super(GIFSplashScreen, self).__init__(**traits)
        self.image_path = image_path
        self._process: Optional[subprocess.Popen] = None

    def open(self) -> None:
        if not os.path.isfile(self.image_path):
            raise OSError("Splash GIF does not exist: {}".format(self.image_path))

        try:
            self._process = subprocess.Popen(
                [sys.executable, "-c", _SPLASH_PROCESS_SCRIPT, self.image_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                close_fds=True,
            )
            self.control = self._process
        except Exception as exc:
            logger.warning("Failed to launch GIF splash process: {}".format(exc))
            self._process = None
            super(GIFSplashScreen, self).open()

    def close(self) -> None:
        if self._process is None:
            super(GIFSplashScreen, self).close()
            return

        try:
            self._process.terminate()
            self._process.wait(timeout=1)
        except Exception:
            try:
                self._process.kill()
            except Exception:
                pass
        finally:
            self._process = None
            self.control = None
