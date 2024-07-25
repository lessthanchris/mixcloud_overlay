import pyautogui
import sqlite3
import eyed3
import time
con = sqlite3.connect("C:/Users/Chris/AppData/Local/Mixxx/mixxxdb.sqlite", check_same_thread=False)


class MixxxCurrentPlaying:
    def __init__(self):
        self.lookup = {}

    def get_window(self):
        all_windows = pyautogui.getAllWindows()
        for window in all_windows:
            if "| Mixxx" not in window.title:
                continue
            return window.title.replace(" | Mixxx", "")

    def get_artist_and_track_from_full(self, full_name):
        split_name = full_name.split(" - ")
        artist = split_name.pop(0)
        track = " - ".join(split_name)
        return artist, track
    
    def get_metadata(self, song_string):
        if not song_string:
            return {}
        if song_string in self.lookup:
            return self.lookup[song_string]
        cur = con.cursor()
        artist, track = self.get_artist_and_track_from_full(song_string)
        query = f"SELECT id FROM library WHERE artist=\"{artist}\" AND title=\"{track}\""
        res = cur.execute(query)
        tracks = res.fetchall()
        for track in tracks:
            track_id, = track
            res = cur.execute(f"SELECT location FROM track_locations WHERE id='{track_id}'")
            try:
                location, = res.fetchone()
            except Exception as e:
                location = None
            if not location:
                continue
            try:
                audiofile = eyed3.load(location)
            except Exception as e: 
                print("audiofile failed with ", e)
                continue
            if not audiofile:
                continue
            if len(audiofile.tag.images[0].image_data) < 10:
                continue
            if audiofile.tag.images[0]._mime_type.decode("utf-8") != "image/jpeg":
                continue
            cur.close()
            data = {
                "artist": audiofile.tag.artist,
                "album": audiofile.tag.album,
                "track": audiofile.tag.title,
                "image_data": audiofile.tag.images[0].image_data
            }
            self.lookup[song_string] = data
            return data
        cur.close()
