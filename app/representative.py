from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, Markup,
    jsonify
)
from werkzeug.security import check_password_hash, generate_password_hash

import logging
from app.db import get_db
from .auth import login_required, load_logged_in_user
from flask_socketio import emit, leave_room, join_room as flask_join_room
from .helpers import str_surround, get_pending_room
import psycopg2
from . import socketio

# Uncomment following line to print DEBUG logs
#  logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

bp = Blueprint('representative', __name__, url_prefix="/representative")


# ROUTES
@bp.route('/get_customers')
@login_required
def get_customers():
    """Find customers according to one of the given keys in GET request,
    return JSON array containing customers."""
    cur = get_db()
    full_name = request.args.get("full_name")
    phone_number = request.args.get("phone_number")
    cust_id = request.args.get("cust_id")

    customers = []
    if full_name:
        cur.execute("""SELECT * FROM wcs.customer WHERE full_name
                ILIKE %s ESCAPE ''""", (str_surround(full_name),))
    elif phone_number:
        cur.execute("""SELECT * FROM wcs.customer WHERE phone_number
                ILIKE %s ESCAPE ''""", (str_surround(phone_number),))
    elif cust_id:
        cur.execute("""SELECT * FROM wcs.customer WHERE cust_id
                = %s""", (cust_id,))

    if full_name or phone_number or cust_id:
        customers = cur.fetchall()

    g.db.commit()
    return jsonify(customers)


@bp.route('/', methods=('GET', 'POST'))
@login_required
def index():
    """Redirect representatives to create_room."""
    return redirect(url_for("representative.create_room"))


@bp.route('/remember-customer', methods=('POST',))
@login_required
def remember_customer():
    """Save customer info to session for future use."""
    customer = request.json.get("customer")
    session["customer"] = customer
    return "success", 200


@bp.route('/create-room', methods=('GET', 'POST'))
@login_required
def create_room():
    """Create a unique meeting room."""
    errors = {}
    # Check if there is existing room in database, update session accordingly
    session["room_id"] = get_pending_room(session["rep_id"])

    if request.method == "POST":
        f = request.form

        if not f["title"]:
            errors["title"] = "is-invalid"
        if not f["password"]:
            errors["password"] = "is-invalid"

        if not errors:
            try:
                cur = get_db()

                customer = f["customer"] or None
                cur.execute("""INSERT INTO wcs.meeting_room (password, rep_id, cust_id, 
                        title, description) VALUES (%s, %s, %s, %s, %s)""",
                            (generate_password_hash(f["password"]), session["rep_id"],
                             customer, f["title"].strip(), f["description"].strip()))

                g.db.commit()
                room_id = get_pending_room(session["rep_id"])
                if room_id:
                    session["room_id"] = room_id
                else:
                    raise Exception("Could not create the room. Please contact the system admin.")

            except psycopg2.errors.IntegrityError:
                flash("You have pending meeting room", "warning")
            except Exception as err:
                flash(str(err), "warning")
            else:
                return redirect(url_for("customer.meeting"))

    return render_template("representative/create_room.html", errors=errors)
