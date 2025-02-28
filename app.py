
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from mixxx import MixxxCurrentPlaying
from flask import send_file
import io
from follower import FollowerAlert
import time
import logging

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, logger=True, engineio_logger=True)
# enable logging in socket.io

mixxx = MixxxCurrentPlaying()

logging.getLogger('socketio').setLevel(logging.DEBUG)
logging.getLogger('engineio').setLevel(logging.DEBUG)

app.logger.debug("Song event received")

@socketio.on('connect')
def connected():
    logging.info("client has connected")
    emit('connect', {'data': 'Connected'})

def send_song_updates():
    while True:
        app.logger.info("HELP")
        try:
            html, image = get_song()
            app.logger.debug(f"Song data: {html}")
            socketio.emit('song', {'html': html, 'image': image})
        except Exception as e:
            app.logger.error(f"Error in song update: {str(e)}")
        socketio.sleep(1)

def send_followers_updates():
    while True:
        try:
            followers = get_followers()
            app.logger.debug(f"Followers data: {followers}")
            socketio.emit('followers', followers)
        except Exception as e:
            app.logger.error(f"Error in followers update: {str(e)}")
        socketio.sleep(5)

@socketio.on('song')
def handle_song_request():
    app.logger.info("Song event received")
    socketio.start_background_task(send_song_updates)

# @socketio.on('song')
# def sendmessage():

#     while True:
#         app.logger.debug("Starting send message")
#         try:
#             html, image = get_song()
#         except:
#             html, image = (None, None)
#         payload = {
#             "html": html,
#             "image": image,
#         }
#         emit('song', payload)
#         time.sleep(1)

# @socketio.on('followers')
# def send_followers():
#     while True:
#         app.logger.debug("Starting send message")
#         followers = get_followers()
#         emit('followers', followers)
#         time.sleep(5)

@socketio.on('followers')
def handle_followers_request():
    app.logger.info("Followers event received")
    socketio.start_background_task(send_followers_updates)

@app.route("/")
def index():
    app.logger.debug("Starting send message")
    return render_template('index.html')

def get_song():
    app.logger.debug("Starting send message")
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

if __name__ == '__main__':
    socketio.run(app, debug=True)
