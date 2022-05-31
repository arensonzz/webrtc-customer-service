from .auth import customer_required
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, Markup
)
from werkzeug.security import check_password_hash, generate_password_hash

import logging
from app.db import get_db
from flask_socketio import emit, leave_room, join_room as flask_join_room
from . import socketio
from .helpers import get_guest_customer

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


@bp.route('/join-meeting/<int:id>', methods=('GET', 'POST'))
@customer_required
def join_meeting(id):
    """Customer joins meeting by entering password."""
    cur = get_db()
    cust_id = None
    errors = {}

    # Check if the room exists
    cur.execute("""SELECT room_id, cust_id, password FROM wcs.meeting_room WHERE room_id = %s""",
                (id,))
    room = cur.fetchone()
    g.db.commit()
    if room is None:
        session.clear()
        flash("The meeting has ended.", "warning")
        return redirect(url_for("customer.index"))

    # Remember customer id if exists
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
        f = request.form
        cur = get_db()
        errors = {}
        # Check password
        # Guest customer form handling
        if g.is_guest:
            # Check for required fields
            if not f["email"] and not f["phone_number"]:
                errors["contact_info"] = "Either email address or phone number must be entered"
            if not f["short_name"]:
                errors["short_name"] = "is-invalid"
            if not f["password"]:
                errors["password"] = "is-invalid"

            # Process form
            if not errors:
                # Block unauthorized access attempts
                if not check_password_hash(room["password"], f["password"]):
                    flash("Password is incorrect.", "warning")
                    return render_template("customer/join_meeting.html", errors=errors)
                # Check if guest exists
                guest_customer = get_guest_customer(f["email"], f["phone_number"])
                if guest_customer is None:
                    # Create new guest in table

                    # Convert blank inputs to None
                    guest_phone = f["phone_number"] or None
                    guest_email = f["email"] or None
                    cur.execute("""INSERT INTO wcs.guest_customer (phone_number, email_address, short_name) VALUES 
                            (%s, %s, %s)""", (guest_phone, guest_email, f["short_name"]))
                    g.db.commit()
                    guest_customer = get_guest_customer(guest_email, guest_phone)

                # Assign the guest customer to the room
                cur.execute("""UPDATE wcs.meeting_room SET g_cust_id = %s WHERE room_id = %s""",
                            (guest_customer["g_cust_id"], g.room_id))
                g.db.commit()
                # Update session
                session["room_id"] = g.room_id
                session["g_cust_id"] = guest_customer["g_cust_id"]
                session["is_guest"] = True
                return redirect(url_for("customer.meeting"))

        # Registered customer form handling
        else:
            # Check for required fields
            if not f["phone_number"]:
                errors["phone_number"] = "is-invalid"
            if not f["password"]:
                errors["password"] = "is-invalid"

            # Process form
            if not errors:
                if not check_password_hash(room["password"], f["password"]):
                    flash("Password is incorrect.", "warning")
                    return render_template("customer/join_meeting.html", errors=errors)
                print("Number:", f["phone_number"])

    return render_template("customer/join_meeting.html", errors=errors)


@bp.route('/meeting', methods=('GET', 'POST'))
def meeting():
    """Page where customer and representative do video chat."""
    if "room_id" not in session:
        flash("You are not in a meeting.", "warning")
        return redirect(url_for("customer.index"))

    # DEBUG VALUES
    flash(f"Room: {session.get('room_id')} | ", "info")
    flash(f"Rep id: {session.get('rep_id')} | ", "info")
    flash(f"Cust id: {session.get('cust_id')} | ", "info")
    flash(f"G cust id: {session.get('g_cust_id')}", "info")
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

    # Clear session
    rep_id = session.get("rep_id")
    session.pop("cust_id", None)
    session.pop("g_cust_id", None)

    # Redirect according to user type (customer and representative)
    if rep_id:
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
