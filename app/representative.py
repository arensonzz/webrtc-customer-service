from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, Markup
)
from werkzeug.security import check_password_hash, generate_password_hash

import logging
from app.db import get_db
from .auth import login_required, load_logged_in_user
from flask_socketio import emit, leave_room, join_room as flask_join_room
from . import socketio

# Uncomment following line to print DEBUG logs
#  logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

# Representative is the root blueprint, no url_prefix specified
bp = Blueprint('representative', __name__)


# ROUTES
@bp.route('/', methods=('GET', 'POST'))
@login_required
def index():
    """Redirect representatives to create_room."""
    return redirect(url_for("representative.create_room"))


@bp.route('/create-room', methods=('GET', 'POST'))
@login_required
def create_room():
    """Create a unique meeting room."""
    if request.method == "POST":
        db = get_db()
        has_error = False
        f = request.form

        if not f["room_name"]:
            flash("Room name is required.", "warning")
            has_error = True

        room_name = f["room_name"].strip().lower()

        if not has_error:
            try:
                db.execute("""INSERT INTO chat_room (created_by_user, name, password, description)
                        VALUES (?, ?, ?, ?)""", (session["user_id"], room_name,
                                                 generate_password_hash(f["password"]),
                                                 f["description"].strip()))
                db.commit()
            except db.IntegrityError:
                message = Markup(f"A room with the name <b>{room_name}</b> already exists.")
                flash(message, "warning")
            else:
                message = Markup(f"Successfully created the room: <b>{room_name}</b>.")
                flash(message, "info")

    return render_template("representative/create_room.html")


@bp.route('/join-room', methods=('GET', 'POST'))
@login_required
def join_room():
    """Let representative join meeting rooms created by him/her."""
    if request.method == "POST":
        cur = get_db()
        f = request.form

    return render_template("representative/join_room.html")


@bp.route('/leave-room')
@login_required
def leave_chat():
    if "room_id" in session:
        session.pop("room_id")
    return redirect(url_for("representative.create_room"))


# SocketIO Events
# Note: namespace is not the same as route. Socket.io namespaces
# just allow you to split logic of application over single shared connection.
# Note: You cannot modify session inside socket.io events. Instead
# create a route and redirect to that route.
