from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, Markup
)
from werkzeug.security import check_password_hash, generate_password_hash

import logging
from app.db import get_db
from flask_socketio import emit, leave_room, join_room as flask_join_room
from . import socketio

# Uncomment following line to print DEBUG logs
#  logging.basicConfig(encoding='utf-8', level=logging.DEBUG)

bp = Blueprint('customer', __name__)


# ROUTES
@bp.route('/', methods=('GET',))
def index():
    """Index page that contains links to each user's interface."""
    return render_template("customer/index.html")


@bp.route('/request-meeting', methods=('GET', 'POST'))
def request_meeting():
    """Customers can request a meeting with the support team."""
    return render_template("customer/request_meeting.html")


@bp.route('/join-meeting/<int:id>', methods=('GET', 'POST'))
def join_meeting(id):
    """Customer joins meeting by entering credentials."""
    return render_template("customer/join_meeting.html")
