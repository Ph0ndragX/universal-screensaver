import sys

from PySide2 import QtWidgets
from PySide2.QtCore import Qt, QUrl, QTimer
from PySide2.QtGui import QPixmap
from PySide2.QtMultimedia import QMediaPlayer, QMediaContent
from PySide2.QtMultimediaWidgets import QVideoWidget
from PySide2.QtWidgets import QVBoxLayout, QStackedWidget

import media_collector

IMG_EXTENSIONS = [".jpg", ".jpeg", ".png"]
VID_EXTENSIONS = [".gif", ".mp4", ".webm"]


class Media:
    def __init__(self, filename):
        self._filename = filename

    def get_filename(self):
        return self._filename

    def is_img(self):
        return any([self._filename.lower().endswith(ext) for ext in IMG_EXTENSIONS])

    def is_vid(self):
        return any([self._filename.lower().endswith(ext) for ext in VID_EXTENSIONS])

    def should_ignore(self):
        return self._filename.lower().endswith("thumbs.db")


class MediaFinder:
    def __init__(self, media_collector):
        self._media_collector = media_collector

    def find_media(self):
        files = self._media_collector.load_media()
        media = [Media(filename) for filename in files if not Media(filename).should_ignore()]

        for m in media:
            if not m.is_img() and not m.is_vid():
                print(f"Failed to determine media type: {m.get_filename()}")
                sys.exit(-1)

        return media


class Orchestrator:
    def __init__(self, stacked_widget, image_view, video_view, media_finder, show_next):
        self._stacked_widget = stacked_widget
        self._image_view = image_view
        self._video_view = video_view
        self._media_finder = media_finder
        self._show_next = show_next

        self._show_next_timer = QTimer()
        self._show_next_timer.setSingleShot(True)
        self._show_next_timer.setInterval(5000)
        self._show_next_timer.timeout.connect(self._show_next)

        self._media = self._media_finder.find_media()
        self._media_idx = 0

    def next(self):
        m = self._media[self._media_idx]
        self._media_idx = self._media_idx + 1
        if self._media_idx == len(self._media):
            self._media_idx = 0

        self._show_next_timer.stop()

        print(f"Playing: {m.get_filename()}")

        if m.is_img():
            self._stacked_widget.setCurrentIndex(0)
            self._image_view.set_media(m)
            self._show_next_timer.start()
        else:
            self._stacked_widget.setCurrentIndex(1)
            self._video_view.set_media(m)


class ImageView(QtWidgets.QLabel):
    def __init__(self, parent):
        super().__init__(parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setContentsMargins(0, 0, 0, 0)
        self.setAlignment(Qt.AlignCenter)

    def set_media(self, media):
        pixmap = QPixmap(media.get_filename())
        if pixmap.isNull():
            print(f"Pixmap is null for: {media.get_filename()}")
        pixmap = pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio)
        self.setPixmap(pixmap)


class VideoView(QtWidgets.QWidget):
    def __init__(self, parent, on_playback_finished):
        super().__init__(parent)

        self._media = None

        self._on_playback_finished = on_playback_finished

        self._media_player = QMediaPlayer(self, QMediaPlayer.VideoSurface)
        self._media_player.setMuted(True)
        self._video_widget = QVideoWidget(self)

        self._layout = QVBoxLayout(self)
        self._layout.addWidget(self._video_widget)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self._layout)

        self._media_player.setVideoOutput(self._video_widget)
        self._media_player.mediaStatusChanged.connect(self.status_changed)
        self._media_player.positionChanged.connect(self.position_changed)

    def set_media(self, media):
        self._media = media
        self._media_player.setMedia(QMediaContent(QUrl.fromLocalFile(media.get_filename())))
        self._media_player.play()

    def status_changed(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self._on_playback_finished()

    def position_changed(self, position):
        # gif position if past its duration, it will probably loop indefinitely, force change
        if position > self._media_player.duration() + 10:
            self._on_playback_finished()

    def flip_muted(self):
        self._media_player.setMuted(not self._media_player.isMuted())


class UniversalScreenSaver(QtWidgets.QMainWindow):
    def __init__(self, args):
        super().__init__()
        self.setWindowFlag(Qt.FramelessWindowHint)

        self._image_view = ImageView(self)
        self._video_view = VideoView(self, self._show_next)

        self._stacked_widget = QStackedWidget(self)
        self._stacked_widget.addWidget(self._image_view)
        self._stacked_widget.addWidget(self._video_view)

        self.setCentralWidget(self._stacked_widget)

        p = self.palette()
        p.setColor(self.backgroundRole(), Qt.black)
        self.setPalette(p)

        self._orchestrator = Orchestrator(
            self._stacked_widget,
            self._image_view,
            self._video_view,
            MediaFinder(media_collector.MediaCollector(args[0])),
            self._show_next
        )

        QTimer.singleShot(0, self._show_next)

    def _show_next(self):
        self._orchestrator.next()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_M:
            self._video_view.flip_muted()
        elif key == Qt.Key_Escape:
            self.close()
        elif key == Qt.Key_Space:
            self._show_next()


if __name__ == "__main__":
    if sys.platform == "linux" or sys.platform == "linux2":
        import pydbus

        pm = pydbus.SessionBus().get("org.freedesktop.PowerManagement", "/org/freedesktop/PowerManagement/Inhibit")
        print(f"Has inhibit: {pm.HasInhibit()}")
        inhibited = pm.Inhibit("Universal ScreenSaver", "Showing images and videos")
        print(f"Has inhibit: {pm.HasInhibit()}")

    app = QtWidgets.QApplication([])
    window = UniversalScreenSaver(sys.argv[1:])
    window.showMaximized()
    sys.exit(app.exec_())
