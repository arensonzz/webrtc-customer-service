from .db import get_db
from flask import g


def str_surround(str: str, surround: str = "%", start=True, end=True):
    """Surround a string with a symbol or another string."""

    if start:
        str = surround + str
    if end:
        str = str + surround
    return str


def get_guest_customer(email, phone_number):
    """Return the guest customer if exists otherwise None."""
    cur = get_db()

    cur.execute("""SELECT * FROM wcs.guest_customer WHERE
            email_address = %s OR phone_number = %s""", (email, phone_number))
    guest_customer = cur.fetchone()
    g.db.commit()
    return guest_customer


if __name__ == "__main__":
    print(str_surround("hello", "__"))
