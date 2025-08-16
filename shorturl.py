from flask import Flask, redirect, abort, render_template_string, send_from_directory
from threading import Thread
import os
import random
import string
import socket

shorturl_app = Flask(__name__)
url_map = {}
reverse_map = {}  # Giúp kiểm tra nếu URL đã tồn tại
server_port = None  # Sẽ được gán khi chọn port

def find_free_port(start=5000, end=6000):
    """Tìm port trống trong khoảng"""
    while True:
        port = random.randint(start, end)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("localhost", port)) != 0:
                return port

def generate_random_key(length=12):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def register_shorturl(url):
    if url in reverse_map:
        short_key = reverse_map[url]
        return f"http://localhost:{server_port}/short/{short_key}"
    
    while True:
        short_key = generate_random_key()
        if short_key not in url_map:
            break

    url_map[short_key] = url
    reverse_map[url] = short_key
    return f"http://localhost:{server_port}/short/{short_key}"

def get_local_file_url(filename):
    return f"http://localhost:{server_port}/access/{filename}"

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
    shorturl_app.run(port=server_port, debug=False, use_reloader=False)

def start_shorturl_thread():
    global server_port
    server_port = find_free_port(10000, 30000) # Tìm port trống trong khoảng từ 10000 đến 30000
    print(f"Short URL server running on port {server_port}")
    flask_thread = Thread(target=run_shorturl_flask)
    flask_thread.daemon = True
    flask_thread.start()