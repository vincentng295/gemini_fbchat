from flask import Flask, redirect, abort, render_template_string, send_from_directory
from threading import Thread
import hashlib
import os

shorturl_app = Flask(__name__)
url_map = {}

def register_shorturl(url):
    short_key = hashlib.md5(url.encode()).hexdigest()[:6]
    url_map[short_key] = url
    return f"http://localhost:5000/short/{short_key}"

def get_local_file_url(filename):
    return f"http://localhost:5000/access/{filename}"

@shorturl_app.route('/short/<short_key>')
def redirect_shorturl(short_key):
    if short_key in url_map:
        return redirect(url_map[short_key])
    else:
        return abort(404)

@shorturl_app.route('/access/<path:filename>')
def serve_file(filename):
    directory = os.path.dirname(filename)  # e.g., "files"
    file_only = os.path.basename(filename)  # e.g., "xxx.jpg"
    # Optional: security check - only allow specific parent directories
    if directory == "files":
        return send_from_directory(directory, file_only)
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
