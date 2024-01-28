import os
import random

import toml

IMG_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]
VID_EXTENSIONS = [".gif", ".mp4", ".webm"]
IGNORED = ["thumbs.db"]


class Media:
    def __init__(self, filename):
        self._filename = filename
        if not (self.is_img() or self.is_vid()):
            raise Exception(f"{filename} is neither a vid or an image")

    def filename(self):
        return self._filename

    def is_img(self):
        return any([self._filename.lower().endswith(ext) for ext in IMG_EXTENSIONS])

    def is_vid(self):
        return any([self._filename.lower().endswith(ext) for ext in VID_EXTENSIONS])


class MediaCollector:

    def __init__(self, settings_file):
        self._settings_file = settings_file
        self._media = None

    def load_media(self):
        if self._media is None:
            self._load_media()
        return self._media

    def _load_media(self):
        with open(self._settings_file, "r") as f:
            self._parse_settings(toml.load(f))

    def _parse_settings(self, settings):
        files = []

        for path in settings["media"]["paths"]:
            print(f"Reading files from {path}")
            found_media = self._find_media_in_path(path)
            print(f"Found {len(found_media)} files")
            files = files + found_media

        order = settings["media"]["order"]
        if order is not None:
            if order == "random":
                random.shuffle(files)
            elif order == "sorted":
                files.sort()

        self._media = [Media(p) for p in files]

    def _find_media_in_path(self, search_dir):
        files = []
        for entry in os.listdir(search_dir):
            filename = os.path.join(search_dir, entry)
            if self._should_ignore(filename):
                continue

            if os.path.isdir(filename):
                files = files + self._find_media_in_path(filename)
            else:
                files.append(filename)

        return files

    def _should_ignore(self, filename):
        ignored = any([filename.lower().endswith(i) for i in IGNORED])
        if ignored:
            print(f"Ignoring file {filename}")
        return ignored
