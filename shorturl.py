from flask import Flask, redirect, abort, render_template_string
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
    if short_key in url_map:
        return redirect(url_map[short_key])
    else:
        return abort(404)

@shorturl_app.errorhandler(404)
def page_not_found(e):
    return render_template_string("""
        <h1>404 Not Found</h1>
        <p>The short URL you're trying to access doesn't exist.</p>
    """), 404

def run_shorturl_flask():
    shorturl_app.run(debug=False, use_reloader=False)

def start_shorturl_thread():
    # Start Flask server in background
    flask_thread = Thread(target=run_shorturl_flask)
    flask_thread.daemon = True
    flask_thread.start()
