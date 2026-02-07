"""Launcher stub for the media server application.

This file keeps backward compatibility for running python app.py.
It imports the app object from the package and runs it.
"""
from src.media_server.app import app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
