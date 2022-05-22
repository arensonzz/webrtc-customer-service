import os
from flask import Flask, redirect, url_for
from flask_session import Session
from flask_socketio import SocketIO

# Create SocketIO instance
socketio = SocketIO(logger=True)


def create_app(test_config=None):
    """Create and return Flask instance"""
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    # Set config values
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flask_group_chat.sqlite'),
        SESSION_TYPE='filesystem',
        SESSION_PERMANENENT=False,
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    # Initialize session
    Session(app)

    # Initialize app with database commands
    from . import db
    db.init_app(app)

    # Initialize SocketIO
    socketio.init_app(app)

    # Register blueprints
    from . import (auth, chat)
    app.register_blueprint(auth.bp)
    app.register_blueprint(chat.bp)
    # Make chat index the root
    app.add_url_rule('/', endpoint='chat.index')

    # A route to test Flask connection
    @app.route('/test')
    def test():
        """Test Flask connection."""
        from . import db
        db = db.get_db()
        return "Server is working.", 200

    return app
