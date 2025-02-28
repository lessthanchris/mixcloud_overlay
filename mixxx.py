import pyautogui
import sqlite3
import eyed3
import logging

from mutagen.flac import FLAC
from enum import Enum

logging.basicConfig(level=logging.DEBUG)

con = sqlite3.connect(
    "C:/Users/Chris/AppData/Local/Mixxx/mixxxdb.sqlite", check_same_thread=False
)


class Filetype(Enum):
    """
    Enum class to represent different file types.
    """

    MP3 = 1
    FLAC = 2
    UNKNOWN = 3


class MixxxCurrentPlaying:
    """
    A class to handle the currently playing track in Mixxx DJ software.
    """

    def __init__(self):
        """
        Initialize the MixxxCurrentPlaying object with an empty lookup dictionary.
        """
        self.lookup = {}

    def get_window(self):
        """
        Get the title of the Mixxx window.

        Returns:
            str: The title of the Mixxx window without the "| Mixxx" suffix.
        """
        all_windows = pyautogui.getAllWindows()
        for window in all_windows:
            if "| Mixxx" not in window.title:
                continue
            logging.info(window.title)
            return window.title.replace(" | Mixxx", "")

    def get_artist_and_track_from_full(self, full_name):
        """
        Split the full track name into artist and track.

        Args:
            full_name (str): The full name of the track in "Artist - Track" format.

        Returns:
            tuple: A tuple containing the artist name and track title.
        """
        split_name = full_name.split(" - ")
        artist = split_name.pop(0)
        track = " - ".join(split_name)
        return artist, track

    def _check_file_type(self, location):
        """
        Check the file type of the audio file at the given location.

        Args:
            location (str): The file path of the audio file.

        Returns:
            Filetype: The detected file type (MP3, FLAC, or UNKNOWN).
        """
        try:
            mp3_audiofile = eyed3.load(location)
        except Exception as e:
            logging.error("MP3 detection failed with ", e)
            return Filetype.UNKNOWN
        if mp3_audiofile:
            return Filetype.MP3
        try:
            flac_audiofile = FLAC(location)
        except Exception as e:
            logging.error(e)
            return Filetype.UNKNOWN
        if flac_audiofile:
            return Filetype.FLAC
        return Filetype.UNKNOWN

    def _get_track_location(self, track):
        """
        Get the file location of a track from the database.

        Args:
            track (tuple): A tuple containing the track ID.

        Returns:
            str or None: The file location of the track, or None if not found.
        """
        (track_id,) = track
        cur = con.cursor()
        res = cur.execute(f"SELECT location FROM track_locations WHERE id='{track_id}'")
        try:
            (location,) = res.fetchone()
        except Exception as e:
            logging.warning("Selecting location for track failed")
            logging.error(e)
            cur.close()
            return None
        cur.close()
        return location

    def _parse_mp3_metadata(self, audiofile):
        """
        Parse metadata from an MP3 file.

        Args:
            audiofile (eyed3.AudioFile): The loaded MP3 audio file.

        Returns:
            dict: A dictionary containing the parsed metadata.
        """
        if not audiofile.tag.images:
            logging.error("There are no images :(")
            image_data = None
        elif len(audiofile.tag.images[0].image_data) < 10:
            logging.warning("There is not enough image data :(")
            image_data = None
        elif audiofile.tag.images[0]._mime_type.decode("utf-8") != "image/jpeg":
            logging.warning("Images are not JPEG")
            image_data = None
        else:
            image_data = audiofile.tag.images[0].image_data
        metadata = {
            "artist": audiofile.tag.artist,
            "album": audiofile.tag.album,
            "track": audiofile.tag.title,
            "image_data": image_data,
        }
        return metadata

    def _parse_flac_metadata(self, audiofile):
        """
        Parse metadata from a FLAC file.

        Args:
            audiofile (mutagen.flac.FLAC): The loaded FLAC audio file.

        Returns:
            dict: A dictionary containing the parsed metadata.
        """
        pictures = audiofile.pictures
        image_data = next(
            (picture.data for picture in pictures if picture.type == 3), None
        )
        data = {
            "artist": audiofile["artist"][0],
            "album": audiofile["album"][0],
            "track": audiofile["title"][0],
            "image_data": image_data,
        }
        return data

    def get_metadata(self, song_string):
        """
        Get metadata for a given song.

        Args:
            song_string (str): The full name of the song in "Artist - Track" format.

        Returns:
            dict: A dictionary containing the song's metadata.
        """
        logging.debug("get_meta is running")
        logging.debug(song_string)
        if not song_string:
            return {}
        if song_string in self.lookup:
            logging.debug("Song data is cached, returning")
            return self.lookup[song_string]
        artist, track = self.get_artist_and_track_from_full(song_string)
        query = f'SELECT id FROM library WHERE artist="{artist}" AND title="{track}"'
        cur = con.cursor()
        res = cur.execute(query)
        tracks = res.fetchall()
        cur.close()
        location = None
        filetype = Filetype.UNKNOWN
        for track in tracks:
            location = self._get_track_location(track)
            if not location:
                continue
            filetype = self._check_file_type(location)
            if filetype != Filetype.UNKNOWN:
                break
        metadata = {}
        match filetype:
            case Filetype.UNKNOWN:
                logging.error("Failed to detect filetype")
            case Filetype.MP3:
                audiofile = eyed3.load(location)
                try:
                    metadata = self._parse_mp3_metadata(audiofile)
                except Exception as e:
                    logging.error("Failed to load MP3 metadata")
                    logging.error(e)
            case Filetype.FLAC:
                audiofile = FLAC(location)
                try:
                    metadata = self._parse_flac_metadata(audiofile)
                except Exception as e:
                    logging.error("Failed to load FLAC metadata")
                    logging.error(e)
        self.lookup[song_string] = metadata
        return metadata
