from flask import Flask, redirect
from threading import Thread
import hashlib

shorturl_app = Flask(__name__)
url_map = {}

def register_shorturl(url):
    short_key = hashlib.md5(url.encode()).hexdigest()[:6]
    url_map[short_key] = url
    return f"http://localhost:5000/{short_key}"

@shorturl_app.route('/<short_key>')
def redirect_shorturl(short_key):
    return redirect(url_map.get(short_key, "/404"))

def run_shorturl_flask():
    shorturl_app.run(debug=False, use_reloader=False)

def start_shorturl_thread():
    # Start Flask server in background
    flask_thread = Thread(target=run_shorturl_flask)
    flask_thread.daemon = True
    flask_thread.start()