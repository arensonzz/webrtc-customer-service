from .db import get_db
from flask import g, session
import phonenumbers
from phonenumbers import carrier
from phonenumbers.phonenumberutil import number_type


def str_surround(str: str, surround: str = "%", start=True, end=True):
    """Surround a string with a symbol or another string."""

    if start:
        str = surround + str
    if end:
        str = str + surround
    return str


def get_guest_customer(email=None, phone_number=None, g_cust_id=None):
    """Find guest_customer with the given email or phone_number from database if g_cust_id
    is given as None. Otherwise find the guest_customer with given g_cust_id."""
    cur = get_db()

    if g_cust_id:
        cur.execute("""SELECT * FROM wcs.guest_customer WHERE
            g_cust_id = %s""", (g_cust_id,))
    else:
        cur.execute("""SELECT * FROM wcs.guest_customer WHERE
                email_address = %s OR phone_number = %s""", (email, phone_number))
    guest_customer = cur.fetchone()
    g.db.commit()
    return guest_customer


def get_customer(cust_id):
    """Find customer with the given id from database."""
    cur = get_db()

    cur.execute("""SELECT * FROM wcs.customer WHERE
            cust_id = %s""", (cust_id,))
    customer = cur.fetchone()
    g.db.commit()
    return customer


def is_phone_valid(phone_number):
    """Check if the phone number is a mobile number following E.164 convention."""
    is_valid = None
    try:
        is_valid = carrier._is_mobile(number_type(phonenumbers.parse(phone_number)))
    except Exception:
        is_valid = False

    return is_valid


def get_pending_room(rep_id):
    """Return the room_id if representative has pending room, otherwise return None."""
    cur = get_db()
    cur.execute("SELECT room_id FROM wcs.meeting_room WHERE rep_id = %s",
                (rep_id,))
    g.db.commit()
    room = cur.fetchone()
    room_id = None
    if room:
        room_id = room.get("room_id")

    return room_id


def meeting_cleanup():
    """Clear meeting information from session."""
    session.pop("room_id", None)
    session.pop("g_cust_id", None)
    session.pop("cust_id", None)
    session.pop("customer", None)
    session.pop("is_guest", None)


def is_room_full(room_id):
    """Check if the meeting room with given id is full. Return True if full, False if not,
    None if the room does not exist."""
    cur = get_db()
    cur.execute("SELECT is_full FROM wcs.meeting_room WHERE room_id = %s",
                (room_id,))
    g.db.commit()
    room = cur.fetchone()
    is_full = None
    if room:
        is_full = room["is_full"]

    return is_full


def set_room_is_full(room_id, is_full):
    """Set is_full column of room to the given value."""
    cur = get_db()
    cur.execute("UPDATE wcs.meeting_room SET is_full = %s WHERE room_id = %s",
                (is_full, room_id))
    print("#######")
    print("####### room_id, is_full: ", room_id, is_full)
    print("#######")
    g.db.commit()


if __name__ == "__main__":
    print("is valid: ", is_phone_valid("+905350285934"))
    print("is valid: ", is_phone_valid("+9053502859345"))
    print("is valid: ", is_phone_valid("+905990285934"))
    print("is valid: ", is_phone_valid("+902580285934"))
