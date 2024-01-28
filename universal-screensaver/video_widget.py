import time

from PySide6.QtCore import QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget


class VideoWidget(QVideoWidget):
    def __init__(self, on_video_finished_playing, minimal_video_duration):
        super(VideoWidget, self).__init__()

        self._on_video_finished_playing = on_video_finished_playing
        self._minimal_video_duration = minimal_video_duration

        self._media_player_audio = QAudioOutput()
        self._media_player_audio.setMuted(True)

        self._media_player = QMediaPlayer()
        self._media_player.setLoops(QMediaPlayer.Loops.Infinite)
        self._media_player.setVideoOutput(self)
        self._media_player.setAudioOutput(self._media_player_audio)
        self._media_player.positionChanged.connect(self._video_position_changed)
        self._media_player.mediaStatusChanged.connect(self._media_status_changed)

        self._video_started_at = None
        self._notify_media_finished = False

    def set_media(self, filename):
        self._video_started_at = time.time()
        self._media_player.setSource(QUrl.fromLocalFile(filename))
        self._media_player.play()

    def stop_and_notify(self):
        self._notify_media_finished = True
        self._media_player.stop()

    def flip_muted(self):
        new_value = not self._media_player_audio.isMuted()
        self._media_player_audio.setMuted(new_value)
        return new_value

    def _video_position_changed(self, position):
        video_showing_for_ms = (time.time() - self._video_started_at) * 1000
        is_video_past_end = position >= self._media_player.duration()

        if is_video_past_end and video_showing_for_ms >= self._minimal_video_duration:
            self._notify_media_finished = True
            self._media_player.stop()

    def _media_status_changed(self, status):
        if status == QMediaPlayer.MediaStatus.LoadedMedia and self._notify_media_finished:
            self._notify_media_finished = False
            self._on_video_finished_playing()
