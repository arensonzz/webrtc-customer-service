import functools
import logging

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, Markup
)
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

# Uncomment following line to print DEBUG logs
#  logging.basicConfig(encoding='utf-8', level=logging.DEBUG)


def login_required(view):
    """Decorator to redirect unauthenticated users back to login page."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            return redirect(url_for('auth.login'))
        return view(**kwargs)

    return wrapped_view


def load_logged_in_user():
    """Return dict of logged in user's informations."""
    user_id = session["user_id"]
    user = None

    if user_id is not None:
        user = get_db().execute("SELECT * FROM user WHERE user_id = ?",
                                (user_id,)).fetchone()

    return user


# ROUTES
@bp.route('/register', methods=('GET', 'POST'))
def register():
    """Register user to database."""
    errors = {}
    if request.method == 'POST':
        f = request.form
        db = get_db()

        if not f["email"]:
            errors["email"] = "Email address is required"

        if not f["password"]:
            errors["password"] = "Password is required"
        elif f["password"] != f["confirmation"]:
            errors["confirmation"] = "Passwords do not match"

        if not f["short_name"]:
            errors["short_name"] = "Short name is required for profile"

        if len(f["short_name"]) > 20:
            errors["short_name"] = "Short name length cannot exceed 20 characters"

        if not errors:
            try:
                db.execute("""INSERT INTO USER (password, email_address, full_name, short_name)
                    VALUES (?, ?, ?, ?)""",
                           (generate_password_hash(f["password"]), f["email"].strip().lower(),
                               f["full_name"].strip(), f["short_name"].strip()))
                db.commit()
            except db.IntegrityError:
                message = Markup(f"User with the email address <b>{f['email']}</b> is already registered.")
                flash(message, "warning")
            else:
                return redirect(url_for("auth.login"))

    return render_template('auth/register.html', errors=errors)


@bp.route('/login', methods=('GET', 'POST'))
def login():
    """Log in user by adding to session."""
    # Redirect to index page if user is already logged in
    if "user_id" in session:
        return redirect(url_for("chat.index"))

    errors = {}
    if request.method == 'POST':
        f = request.form
        db = get_db()
        is_bad_login = False
        errors = {}

        if not f["email"]:
            errors["email"] = "Email address is required"

        if not f["password"]:
            errors["password"] = "Password is required"

        if not errors:
            user = db.execute("""SELECT user_id, email_address, password FROM user 
                    WHERE email_address = ?""", (f["email"].strip().lower(),)).fetchone()

            if user is None:
                is_bad_login = True
                logging.debug("Provided email address do not exist in the `user` table")
            elif not check_password_hash(user["password"], f["password"]):
                is_bad_login = True
                logging.debug("Password is incorrect")

            if is_bad_login:
                flash("Email address or password is incorrect.", "warning")
            elif not errors:
                # Add the user info to session
                # User stays logged in this way
                session.clear()
                session["user_id"] = user["user_id"]
                return redirect(url_for("chat.index"))
    return render_template('auth/login.html', errors=errors)


@bp.route('/logout')
def logout():
    """Log out user by removing info from session."""
    session.clear()
    return redirect(url_for("chat.index"))
