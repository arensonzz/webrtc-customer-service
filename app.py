from flask_socketio import SocketIO
from app import create_app, socketio


app = create_app()

if __name__ == "__main__":
    # Uncomment following line to import SSL certificates to the development server.
    # You should have self-signed certificates ready in the `certificate` directory.
    socketio.run(app, ssl_context='adhoc')
    #  socketio.run(app)
