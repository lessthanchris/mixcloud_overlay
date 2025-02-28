import pyautogui
import sqlite3
import eyed3
import time
con = sqlite3.connect("C:/Users/Chris/AppData/Local/Mixxx/mixxxdb.sqlite", check_same_thread=False)
import logging
from mutagen.flac import FLAC

logging.basicConfig(level=logging.DEBUG)

class MixxxCurrentPlaying:
    def __init__(self):
        self.lookup = {}

    def get_window(self):
        all_windows = pyautogui.getAllWindows()
        for window in all_windows:
            if "| Mixxx" not in window.title:
                continue
            logging.info(window.title)
            return window.title.replace(" | Mixxx", "")

    def get_artist_and_track_from_full(self, full_name):
        split_name = full_name.split(" - ")
        artist = split_name.pop(0)
        track = " - ".join(split_name)
        print(artist,track)
        return artist, track
    
    def get_metadata(self, song_string):
        logging.debug("this is running")
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
                logging.error("audiofile failed with ", e)
                continue
            if not audiofile:
                logging.error("This is not an audiofile")
                try:
                    audio = FLAC(location)
                    logging.info(audio.pprint())
                    pictures = audio.pictures
                    image_data = None
                    for pic in pictures:
                        if pic.type == 3:
                            logging.info("PICTURE HAS BEEN FOUND!")
                            image_data = pic.data
                            break
                    data = {
                        "artist": audio["artist"][0],
                        "album": audio["album"][0],
                        "track": audio["title"][0],
                        "image_data": image_data
                    }
                    self.lookup[song_string] = data
                    return data
                except:
                    logging.info("This is also not flac")
                    continue
                logging.error(audiofile)
                continue
            if not audiofile.tag.images or len(audiofile.tag.images[0].image_data) < 10:
                logging.error("There are no images :(")
                images = None
            else:
                images = audiofile.tag.images[0].image_data
            if not audiofile.tag.images or audiofile.tag.images[0]._mime_type.decode("utf-8") != "image/jpeg":
                logging.error("There are no images :(")
                images = None
            cur.close()
            data = {
                "artist": audiofile.tag.artist,
                "album": audiofile.tag.album,
                "track": audiofile.tag.title,
                "image_data": images
            }
            self.lookup[song_string] = data
            return data
        cur.close()
