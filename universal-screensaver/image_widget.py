from PySide6 import QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor, QPixmap
from PySide6.QtWidgets import QLabel


class ImageWidget(QLabel):
    def __init__(self):
        super(ImageWidget, self).__init__()
        self.setContentsMargins(0, 0, 0, 0)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Expanding)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("black"))
        self.setPalette(palette)

    def set_media(self, media):
        pixmap = QPixmap(media.filename())
        if pixmap.isNull():
            print(f"Pixmap is null for: {media.filename()}")
            return
        pixmap = pixmap.scaled(self.width(), self.height(), Qt.AspectRatioMode.KeepAspectRatio)
        self.setPixmap(pixmap)
