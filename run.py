"""Start the web app:  python run.py   (from the project root)"""
import sys

print("Python:", sys.version.split()[0], flush=True)
print("Loading app...", flush=True)

from Backend.app import app

print("App loaded. Open http://127.0.0.1:5000 in your browser.", flush=True)
print("Press Ctrl+C to stop.", flush=True)
app.run(host="127.0.0.1", port=5000, debug=False)
print("Server stopped.", flush=True)
