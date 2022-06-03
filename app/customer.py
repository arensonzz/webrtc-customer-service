from .auth import customer_required
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, Markup
)
from werkzeug.security import check_password_hash, generate_password_hash

import logging
from app.db import get_db
from flask_socketio import emit, leave_room, join_room, rooms
from . import socketio
from .helpers import get_guest_customer, is_phone_valid, get_customer


# Uncomment following line to print DEBUG logs
logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

bp = Blueprint('customer', __name__)


# ROUTES
@bp.route('/', methods=('GET',))
def index():
    """Index page that contains links to each user type's interfaces."""
    # Redirect logged in representatives to representative index page
    if "rep_id" in session:
        return redirect(url_for("representative.index"))
    else:
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

    # Redirect customer to the ongoin meeting if there is one
    if "room_id" in session:
        flash("You have ongoing meeting.", "warning")
        return redirect(url_for("customer.meeting"))

    # Check if the room exists
    cur.execute("""SELECT room_id, cust_id, password FROM wcs.meeting_room WHERE room_id = %s""",
                (id,))
    room = cur.fetchone()
    g.db.commit()
    if room is None:
        flash("The meeting has ended.", "warning")
        return redirect(url_for("customer.index"))

    # Remember customer id if exists
    cust_id = room["cust_id"]

    # Declare customer type
    g.is_guest = True if cust_id is None else False

    # Remember the dynamic id to access from the HTML
    if "room_id" not in g:
        g.room_id = id

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
            # Validate phone number
            elif not is_phone_valid(f["phone_number"]):
                errors["phone_number_check"] = "is-invalid"
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
                # Create new guest in table if guest does not exist
                if guest_customer is None:

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
                # Correct inputs
                # Update session
                session["room_id"] = g.room_id
                session["g_cust_id"] = guest_customer["g_cust_id"]
                session.pop("cust_id", None)
                session["is_guest"] = True
                return redirect(url_for("customer.meeting"))

        # Registered customer form handling
        else:
            # Check for required fields
            if not f["phone_number"]:
                errors["phone_number"] = "is-invalid"
            # Validate phone number
            elif not is_phone_valid(f["phone_number"]):
                errors["phone_number_check"] = "is-invalid"
            if not f["password"]:
                errors["password"] = "is-invalid"

            # Process form
            if not errors:
                if not check_password_hash(room["password"], f["password"]):
                    flash("Password is incorrect.", "warning")
                    return render_template("customer/join_meeting.html", errors=errors)

                customer = get_customer(room["cust_id"])
                if customer["phone_number"] != f["phone_number"]:
                    flash("Phone number is incorrect.", "warning")
                    return render_template("customer/join_meeting.html", errors=errors)
                # Correct inputs
                # Update session
                session["room_id"] = g.room_id
                session["cust_id"] = customer["cust_id"]
                session.pop("g_guest_id", None)
                session["is_guest"] = False
                return redirect(url_for("customer.meeting"))

    return render_template("customer/join_meeting.html", errors=errors)


@bp.route('/meeting', methods=('GET', 'POST'))
def meeting():
    """Page where customer and representative do video chat."""
    if "room_id" not in session:
        flash("You are not in a meeting.", "warning")
        return redirect(url_for("customer.index"))

    # Check if the room exists
    cur = get_db()
    cur.execute("SELECT room_id FROM wcs.meeting_room WHERE room_id = %s", (session["room_id"],))
    g.db.commit()
    if cur.fetchone() is None:
        flash("The meeting has ended.", "warning")
        # Clear room from the session
        session.pop("cust_id", None)
        session.pop("g_cust_id", None)
        session.pop("room_id", None)
        session.pop("is_guest", None)
        return redirect(url_for("customer.index"))

    # DEBUG VALUES
    #  flash(f"Room: {session.get('room_id')} | ", "info")
    #  flash(f"Rep id: {session.get('rep_id')} | ", "info")
    #  flash(f"Cust id: {session.get('cust_id')} | ", "info")
    #  flash(f"G cust id: {session.get('g_cust_id')}", "info")
    return render_template("customer/meeting.html")


@bp.route('/leave-meeting')
def leave_meeting():
    """Route which clears session and leaves the meeting."""
    if "room_id" in session:
        # Clear session
        room_id = session.pop("room_id")
        session.pop("g_cust_id", None)
        session.pop("cust_id", None)
        customer = session.pop("customer", None)
        # Get names and flash info message
        message = Markup(f"The meeting with the id <b>{room_id}</b> has ended.")
        if "rep_id" in session and customer is not None:
            name = customer["short_name"]
            if "cust_id" in customer:
                name = customer["full_name"]

            message = Markup(f"The meeting with <b>{name}</b> has ended.")

        # Delete room from the database
        cur = get_db()
        cur.execute("""DELETE FROM wcs.meeting_room WHERE room_id = %s""",
                    (room_id,))
        g.db.commit()

        flash(message, "info")
    else:
        flash("You are not in a meeting.", "warning")

    # Redirect according to user type (customer and representative)
    return redirect(url_for("customer.index"))


# SocketIO Events
# Note: namespace is not the same as route. Socket.io namespaces
# just allow you to split logic of application over single shared connection.
# Note: You cannot modify session inside socket.io events. Instead
# create a route and redirect to that route.
@socketio.on('connect', namespace="/meeting")
def on_connect():
    """Test SocketIO connection by passing message between server and client."""
    logging.debug("SocketIO: Connected to client")


@socketio.on('joined', namespace="/meeting")
def on_joined():
    """Sent by clients after they connect to socket.io and finish their on connect event."""
    room_id = session["room_id"]
    join_room(room_id)
    # Send different data according to the connected user type
    is_rep = False
    customer = None
    if "rep_id" in session:
        is_rep = True
    else:
        if session["is_guest"]:
            customer = get_guest_customer(g_cust_id=session["g_cust_id"])
        else:
            customer = get_customer(session["cust_id"])

    # Alert other clients of the joining client
    emit("client joined", {'is_rep': is_rep, 'is_guest': session.get("is_guest"),
                           'customer': customer}, to=room_id, include_self=False)


@socketio.on('left', namespace="/meeting")
def on_left(message):
    """Sent by clients when they leave a room."""
    room = session['room_id']
    leave_room(room)
    emit("end meeting", room=room)


@socketio.on('disconnect', namespace="/meeting")
def on_disconnect():
    """Sent by clients when they disconnect from the socket."""
    print("### Client disconnected")
    #  room = session['room_id']
    #  emit("end meeting", include_self=False, room=room)
