from .db import get_db
from flask import g
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


def get_guest_customer(email, phone_number):
    """Find guest_customer with the given email or phone_number from database."""
    cur = get_db()

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


if __name__ == "__main__":
    print("is valid: ", is_phone_valid("+905350285934"))
    print("is valid: ", is_phone_valid("+9053502859345"))
    print("is valid: ", is_phone_valid("+905990285934"))
    print("is valid: ", is_phone_valid("+902580285934"))
