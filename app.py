from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from mixxx import MixxxCurrentPlaying
from flask import send_file
import io
from follower import FollowerAlert
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)
mixxx = MixxxCurrentPlaying()

if __name__ == '__main__':
    socketio.run(app)

@socketio.on('connect')
def connected():
    print("client has connected")
    emit('connect', {'data': 'Connected'})

@socketio.on('song')
def sendmessage():
    print("Starting send message")
    while True:
        try:
            html, image = get_song()
        except:
            html, image = (None, None)
        payload = {
            "html": html,
            "image": image,
        }
        emit('song', payload)

@socketio.on('followers')
def send_followers():
    print("Starting send followers")
    while True:
        followers = get_followers()
        emit('followers', followers)

@app.route("/")
def index():
    return render_template('index.html')

def get_song():
    song_string = mixxx.get_window()
    if not song_string:
        return
    metadata = mixxx.get_metadata(song_string)
    if not metadata:
        return
    artist = metadata.get("artist", "")
    track = metadata.get("track", "")
    song = metadata.get("song", "")
    html = f"<h1><span class='song_info' id='song_artist'>{ artist }</span>"
    html += f"<span class='song_info' id='song_title'>{ track }</span>"
    html += f"<span class='song_info' id='song_album'>{ song }</span></h1>"
    image = f'<img id="art" src="/api/get_image/{ metadata["track"]}" width="300px" height="300px">'
    return (html, image) 

@app.route("/api/get_image/<track>")
def get_image(track):
    song_string = mixxx.get_window()
    if not song_string:
        return {}
    metadata = mixxx.get_metadata(song_string)
    image_data = metadata['image_data']
    return send_file(
        io.BytesIO(image_data),
        mimetype='image/jpeg',
        as_attachment=False
    )

def get_followers():
    follower_alert = FollowerAlert()
    followers =  follower_alert.get_followers()
    return f"Mixcloud Followers: {len(followers)}"
