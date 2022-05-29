from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, Markup
)
from werkzeug.security import check_password_hash, generate_password_hash

import logging
from app.db import get_db
from flask_socketio import emit, leave_room, join_room as flask_join_room
from . import socketio
from .auth import customer_required

# Uncomment following line to print DEBUG logs
#  logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

bp = Blueprint('customer', __name__)


# ROUTES
@bp.route('/', methods=('GET',))
def index():
    """Index page that contains links to each user type's interfaces."""
    if "rep_id" in session:
        return redirect(url_for("representative.index"))
    return render_template("customer/index.html")


@bp.route('/request-meeting', methods=('GET', 'POST'))
@customer_required
def request_meeting():
    """Customers can request a meeting with the support team."""
    return render_template("customer/request_meeting.html")


@bp.route('/join-meeting/<int:id>', methods=('GET', 'POST'))
@customer_required
def join_meeting(id):
    """Customer joins meeting by entering credentials."""
    cur = get_db()

    # Remember the dynamic id to access from the HTML
    if "room_id" not in g:
        g.room_id = id

    # Get the customer info from the room record if not guest customer
    if "cust_id" not in session and "is_guest_customer" not in session:
        cur.execute("""SELECT cust_id FROM wcs.meeting_room WHERE room_id = %s""",
                    (id,))
        cust_id = cur.fetchone()
        g.db.commit()
        if cust_id is not None:
            session["cust_id"] = cust_id
        else:
            session["is_guest_customer"] = True

    if request.method == "POST":
        pass

    return render_template("customer/join_meeting.html")


@bp.route('/meeting', methods=('GET', 'POST'))
def meeting():
    """Page where customer and representative do video chat."""
    if "room_id" not in session:
        flash("You are not in a meeting.", "warning")
        return redirect(url_for("customer.index"))
    return render_template("customer/meeting.html")


@bp.route('/leave-meeting')
def leave_meeting():
    """Route which clears session and leaves the meeting."""
    if "room_id" in session:
        # Clear room_id from session
        room_id = session.pop("room_id")
        # Delete room from the database
        with get_db() as cur:
            cur.execute("""DELETE FROM wcs.meeting_room WHERE room_id = %s""",
                        (room_id,))
            g.db.commit()

    # Redirect according to user type (customer and representative)
    if "rep_id" in session:
        return redirect(url_for("representative.index"))
    else:
        return redirect(url_for("customer.index"))


# SocketIO Events
# Note: namespace is not the same as route. Socket.io namespaces
# just allow you to split logic of application over single shared connection.
# Note: You cannot modify session inside socket.io events. Instead
# create a route and redirect to that route.
@socketio.on('connect', namespace="/meeting")
def test_connect():
    """Test SocketIO connection by passing message between server and client."""
    logging.debug("SocketIO: Connected to client")


@socketio.on('leave', namespace="/meeting")
def left(message):
    """Sent by clients when they leave a room."""
    room = session['room_id']
    leave_room(room)
    emit("end", room=room)
