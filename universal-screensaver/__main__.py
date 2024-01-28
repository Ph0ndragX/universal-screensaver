import sys

from PySide6.QtCore import QTimer
from PySide6.QtGui import Qt, QPalette, QColor
from PySide6.QtWidgets import QApplication, QStackedLayout, QMainWindow, QWidget

from image_widget import ImageWidget
from media import MediaCollector
from video_widget import VideoWidget


class UniversalScreensaver(QMainWindow):
    def __init__(self, media_collector, default_image_timeout_ms=5000):
        super(UniversalScreensaver, self).__init__()

        self._default_image_timeout_ms = default_image_timeout_ms

        self.setContentsMargins(0, 0, 0, 0)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("black"))
        self.setPalette(palette)

        self._media_idx = -1
        self._media = media_collector.load_media()

        self._image_widget = ImageWidget()
        self._video_widget = VideoWidget(self._video_finished_playing, self._default_image_timeout_ms)

        self._layout = QStackedLayout(self)
        self._layout.addWidget(self._image_widget)
        self._layout.addWidget(self._video_widget)

        self._central_widget = QWidget()
        self._central_widget.setLayout(self._layout)
        self.setCentralWidget(self._central_widget)

        self._show_next_timer = QTimer()
        self._show_next_timer.setSingleShot(True)
        # noinspection PyUnresolvedReferences
        self._show_next_timer.timeout.connect(self._show_next)
        self._schedule_next_change()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key.Key_Escape:
            sys.exit()
        elif key == Qt.Key.Key_Space:
            media = self._current_media()
            if media.is_img():
                self._schedule_next_change()
            else:
                self._video_widget.stop_and_notify()
        elif key == Qt.Key.Key_M:
            new_muted = self._video_widget.flip_muted()
            print(f"Is audio muted: {new_muted}")

    def _get_next_media(self):
        self._media_idx = (self._media_idx + 1) % len(self._media)
        return self._current_media()

    def _current_media(self):
        return self._media[self._media_idx]

    def _show_next(self):
        self._show_next_timer.stop()

        media = self._get_next_media()
        print(f"Showing: {media.filename()}")
        if media.is_img():
            self._image_widget.set_media(media)
            self._layout.setCurrentIndex(0)
            self._schedule_next_change(self._default_image_timeout_ms)
        else:
            self._video_widget.set_media(media.filename())
            self._layout.setCurrentIndex(1)

    def _video_finished_playing(self):
        self._schedule_next_change()

    def _schedule_next_change(self, interval=1):
        self._show_next_timer.setInterval(interval)
        self._show_next_timer.start()


if __name__ == "__main__":
    if sys.platform == "linux" or sys.platform == "linux2":
        import pydbus

        pm = pydbus.SessionBus().get("org.freedesktop.PowerManagement", "/org/freedesktop/PowerManagement/Inhibit")
        print(f"Has inhibit: {pm.HasInhibit()}")
        inhibited = pm.Inhibit("Universal ScreenSaver", "Showing images and videos")
        print(f"Has inhibit: {pm.HasInhibit()}")

    mc = MediaCollector(sys.argv[1])

    app = QApplication(sys.argv)

    screensaver = UniversalScreensaver(mc, default_image_timeout_ms=10_000)
    screensaver.showFullScreen()

    app.exec()
