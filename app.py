from flask import Flask, render_template
from flask_socketio import SocketIO
from mixxx import MixxxCurrentPlaying
from flask import send_file
import io
from follower import FollowerAlert
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketIO = SocketIO(app)

if __name__ == '__main__':
    socketio.run(app)

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/api/get_song")
def get_song():
    mixxx = MixxxCurrentPlaying()
    song_string = mixxx.get_window()
    try: 
        metadata = mixxx.get_metadata(song_string)
    except:
        metadata = {}
    artist = metadata.get("artist", "")
    track = metadata.get("track", "")
    song = metadata.get("song", "")
    html = f"<span class='song_info' id='song_artist'>{ artist }</span>"
    html += f"<span class='song_info' id='song_title'>{ track }</span>"
    html += f"<span class='song_info' id='song_album'>{ song }</span>"
    return html

@app.route("/api/get_image_html")
def get_image_html():
    mixxx = MixxxCurrentPlaying()
    song_string = mixxx.get_window()
    if not song_string:
        return ""
    metadata = mixxx.get_metadata(song_string, return_image=True)
    return f"<img id='art' src='/api/get_image/{ metadata['track']}' width='300px' height='300px'></img>"

@app.route("/api/get_image/<track>")
def get_image(track):
    mixxx = MixxxCurrentPlaying()
    song_string = mixxx.get_window()
    if not song_string:
        return {}
    metadata = mixxx.get_metadata(song_string, return_image=True)
    image_data = metadata['image_data']
    return send_file(
        io.BytesIO(image_data),
        mimetype='image/jpeg',
        as_attachment=False
    )

@app.route("/api/get_followers")
def get_followers():
    follower_alert = FollowerAlert()
    followers =  follower_alert.get_followers()
    return f"Mixcloud Followers: {len(followers)}"
