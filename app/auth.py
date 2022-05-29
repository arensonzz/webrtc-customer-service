import functools
import logging

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, Markup
)
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db
import psycopg2

bp = Blueprint('auth', __name__, url_prefix='/auth')

# Uncomment following line to print DEBUG logs
#  logging.basicConfig(encoding='utf-8', level=logging.DEBUG)


def login_required(view):
    """Decorator to redirect unauthenticated representatives back to login page."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if "rep_id" not in session:
            flash("You must first login to access that page.", "warning")
            return redirect(url_for('auth.login'))
        return view(**kwargs)

    return wrapped_view


def customer_required(view):
    """Decorator to redirect representatives back to index page."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if "rep_id" in session:
            flash("The route you tried to access is for customers only.", "warning")
            return redirect(url_for('representative.index'))
        return view(**kwargs)

    return wrapped_view


def load_logged_in_user():
    """Return dict of logged in representative's informations."""
    rep_id = session["rep_id"]
    user = None

    if rep_id is not None:
        with get_db() as cur:
            cur.execute("SELECT * FROM wcs.representative WHERE rep_id = %s",
                        (rep_id,))
            user = cur.fetchone()
            g.db.commit()

    return user


# ROUTES
@bp.route('/register', methods=('GET', 'POST'))
def register():
    """Register representative to database."""
    # Redirect to index page if user is logged in
    if "rep_id" in session:
        return redirect(url_for("representative.index"))

    errors = {}
    if request.method == 'POST':
        f = request.form
        cur = get_db()

        if not f["email"]:
            errors["email"] = "Email address is required"

        if not f["password"]:
            errors["password"] = "Password is required"
        elif f["password"] != f["confirmation"]:
            errors["confirmation"] = "Passwords do not match"

        if not f["short_name"]:
            errors["short_name"] = "Short name is required for profile"

        if not f["full_name"]:
            errors["full_name"] = "Full name is required as identity information"

        if not errors:
            try:
                cur.execute("""INSERT INTO wcs.representative (password, email_address, full_name, short_name)
                    VALUES (%s, %s, %s, %s)""",
                            (generate_password_hash(f["password"]), f["email"].strip().lower(),
                             f["full_name"].strip(), f["short_name"].strip()))
                g.db.commit()
            except psycopg2.errors.IntegrityError:
                message = Markup(f"User with the email address <b>{f['email']}</b> is already registered.")
                flash(message, "warning")
            else:
                flash("You have successfully registered.", "info")
                return redirect(url_for("auth.login"))
            finally:
                cur.close()

    return render_template('auth/register.html', errors=errors)


@bp.route('/login', methods=('GET', 'POST'))
def login():
    """Log in representative by adding to session."""
    # Redirect to index page if user is already logged in
    if "rep_id" in session:
        return redirect(url_for("representative.index"))

    errors = {}
    if request.method == 'POST':
        f = request.form
        cur = get_db()
        is_bad_login = False
        errors = {}

        if not f["email"]:
            errors["email"] = "Email address is required"

        if not f["password"]:
            errors["password"] = "Password is required"

        if not errors:
            cur.execute("""SELECT rep_id, email_address, password FROM wcs.representative 
                    WHERE email_address = %s""", (f["email"].strip(),))
            user = cur.fetchone()
            g.db.commit()
            cur.close()

            if user is None:
                is_bad_login = True
                logging.debug("Provided email address do not exist in the `wcs.representative` table")
            elif not check_password_hash(user["password"], f["password"]):
                is_bad_login = True
                logging.debug("Password is incorrect")

            if is_bad_login:
                flash("Email address or password is incorrect.", "warning")
            elif not errors:
                # Add the user info to session
                # User stays logged in this way
                session.clear()
                session["rep_id"] = user["rep_id"]
                return redirect(url_for("representative.index"))
    return render_template('auth/login.html', errors=errors)


@bp.route('/logout')
def logout():
    """Log out representative by removing info from session."""
    session.clear()
    return redirect(url_for("auth.login"))
