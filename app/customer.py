from .auth import customer_required
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, Markup
)
from werkzeug.security import check_password_hash

import logging
from app.db import get_db
from flask_socketio import emit, leave_room, join_room
from . import socketio
from .helpers import get_guest_customer, is_phone_valid, get_customer, meeting_cleanup, is_room_full, set_room_is_full
from datetime import datetime

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

    # Check room for capacity
    if is_room_full(id):
        flash("There are already two people connected to this meeting.", "warning")
        return redirect(url_for("customer.index"))

    # Redirect customer to the ongoing meeting if id's match
    # otherwise clean meeting from session
    if "room_id" in session and session["room_id"] == id:
        flash("You reconnected to the meeting.", "warning")
        return redirect(url_for("customer.meeting"))
    else:
        meeting_cleanup()

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
        meeting_cleanup()
        return redirect(url_for("customer.index"))

    return render_template("customer/meeting.html")


@bp.route('/set-room-vacancy', methods=('POST',))
def set_room_vacancy():
    """Change is_full status of room according to information inf POST request."""
    if "room_id" not in session:
        flash("Your are not authorized for this.", "warning")
        return redirect(url_for("customer.index"))

    is_full = request.json.get("is_full")
    room_id = session["room_id"]
    set_room_is_full(room_id, is_full)
    return "success", 200


@bp.route('/leave-meeting')
def leave_meeting():
    """Route which clears session and leaves the meeting."""
    if "room_id" in session:
        # Create call log if the video chat has been initiated
        if "rep_id" in session and session.get("call_start_timestamp"):
            # Create call log
            cur = get_db()
            customer = session.get("customer")
            call_start_timestamp = session.get("call_start_timestamp")
            camera_on_ms = session.get("camera_on_ms")
            mic_on_ms = session.get("mic_on_ms")
            camera_on_secs = 0
            mic_on_secs = 0
            if camera_on_ms is not None:
                camera_on_secs = round(camera_on_ms / 1000)
            if mic_on_ms is not None:
                mic_on_secs = round(mic_on_ms / 1000)
            call_length_secs = round(int(datetime.timestamp(datetime.now())) - int(call_start_timestamp) / 1000)
            cust_id = None if customer is None else customer.get("cust_id")
            g_cust_id = None if customer is None else customer.get("g_cust_id")
            cur.execute("""INSERT INTO wcs.call_log (rep_id, cust_id, g_cust_id, 
                call_start_timestamp, call_length_secs, active_talked_secs, camera_on_secs)
                VALUES (%s, %s, %s, %s, %s, %s, %s)""", (session.get("rep_id"), cust_id,
                                                         g_cust_id, call_start_timestamp, call_length_secs, mic_on_secs,
                                                         camera_on_secs))
            g.db.commit()
        room_id = session["room_id"]
        customer = session.get("customer")
        # Clear session
        meeting_cleanup()

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
            customer["is_guest"] = True
        else:
            customer = get_customer(session["cust_id"])
            customer["is_guest"] = False

    # Alert other clients of the joining client
    emit("client joined", {'is_rep': is_rep, 'customer': customer}, to=room_id, include_self=False)


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


@socketio.on('webrtc offer', namespace="/meeting")
def on_webrtc_offer(data):
    """Sent by clients when they create an SDP offer to start the call."""
    room = session['room_id']
    emit("webrtc offer", data, include_self=False, room=room)


@socketio.on('webrtc answer', namespace="/meeting")
def on_webrtc_answer(data):
    """Sent by clients when they create an SDP answer to pick up the call."""
    room = session['room_id']
    emit("webrtc answer", data, include_self=False, room=room)


@socketio.on('webrtc ice candidate', namespace="/meeting")
def on_webrtc_ice_candidate(data):
    """Sent by clients when they create an ICE candidate."""
    room = session['room_id']
    emit("webrtc ice candidate", data, include_self=False, room=room)


@socketio.on('start call', namespace="/meeting")
def on_start_call():
    """Sent by clients when they want to initiate the call."""
    room = session['room_id']
    emit("start call", include_self=False, room=room)


@socketio.on('call accepted', namespace="/meeting")
def on_call_accepted():
    """Sent by clients when they accept the call request."""
    room = session['room_id']
    emit("call accepted", include_self=False, room=room)


@socketio.on('call rejected', namespace="/meeting")
def on_call_rejected():
    """Sent by clients when they reject the call request."""
    room = session['room_id']
    emit("call rejected", include_self=False, room=room)


@socketio.on('too many device connected', namespace="/meeting")
def on_too_many_device_connected():
    """Sent by clients when third device tries to join the call."""
    room = session['room_id']
    emit("too many device connected", include_self=False, room=room)
