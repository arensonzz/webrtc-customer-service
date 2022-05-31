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
    # Redirect logged in representatives to representative index page
    if "rep_id" in session:
        return redirect(url_for("representative.index"))
    return render_template("customer/index.html")


@bp.route('/request-meeting', methods=('GET', 'POST'))
@customer_required
def request_meeting():
    """Customers can request a meeting with the support team."""
    return render_template("customer/request_meeting.html")


@bp.route('/guest-entry/<room_id>/<is_guest>', methods=('POST',))
@customer_required
def guest_entry(room_id, is_guest):
    """Registers the guest customer and checks the entered room password."""
    f = request.form
    cur = get_db()
    errors = {}

    if not is_guest:
        flash("You are not authorized to access that page.", "warning")
        return redirect(url_for("customer.index"))

    if not f["email"] and not f["phone_number"]:
        errors["contact_info"] = "Either email address or phone number must be entered"
    if not f["short_name"]:
        errors["short_name"] = "is-invalid"
    if not f["password"]:
        errors["password"] = "Password is required"

    # TODO
    g.room_id = room_id
    g.is_guest = is_guest
    return render_template("customer/join_meeting.html", errors=errors)


@bp.route('/join-meeting/<int:id>', methods=('GET', 'POST'))
@customer_required
def join_meeting(id):
    """Customer joins meeting by entering password."""
    cur = get_db()
    cust_id = None
    errors = {}

    # Check if the room exists
    cur.execute("""SELECT room_id, cust_id FROM wcs.meeting_room WHERE room_id = %s""",
                (id,))
    room = cur.fetchone()
    g.db.commit()
    if room is None:
        session.clear()
        flash("The meeting has ended.", "warning")
        return redirect(url_for("customer.index"))

    cust_id = room["cust_id"]

    # Remember the dynamic id to access from the HTML
    if "room_id" not in g:
        g.room_id = id
    # Remember the customer type
    if "is_guest" not in g:
        g.is_guest = False

    # Get the customer info from the room record if not guest customer
    if "cust_id" not in session and not g.is_guest:
        # Declare as guest customer
        if cust_id is None:
            g.is_guest = True

    if request.method == "POST":
        # TODO
        pass

    return render_template("customer/join_meeting.html", errors=errors)


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
