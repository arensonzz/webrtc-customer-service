from flask_socketio import SocketIO
from app import create_app, socketio
import os


app = create_app()

if __name__ == "__main__":

    # Make sure env variables are set
    if not os.environ.get("HTTPS_MODE"):
        raise RuntimeError("HTTPS_MODE not set.\n\tOptions: \"self-signed\", \"adhoc\", \"none\".")

    https_mode = os.environ.get("HTTPS_MODE").lower()

    if https_mode == "self-signed":
        # You should have self-signed certificates ready in the `certificate` directory.
        socketio.run(app, ssl_context=('certificate/fullchain.pem', 'certificate/cert-key.pem'))
    elif https_mode == "adhoc":
        # Mock HTTPS server
        # You need to install `pyopenssl` package to use this option
        socketio.run(app, ssl_context='adhoc')
    elif https_mode == "none":
        # HTTP server instead of HTTPS
        socketio.run(app)
    else:
        raise RuntimeError("Unknown HTTPS_MODE option.")
