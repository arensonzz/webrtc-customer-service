import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext


def get_db() -> sqlite3.Connection:
    """Connect to sqlite3 database and return connection."""
    if 'db' not in g:
        # `g` object is used to store connection for multiple access to a data
        # during a request
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        # Return rows that act like dicts
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    """Close database connection if it exists."""
    db = g.pop('db', None)

    if db is not None:
        db.close()


def import_sql(filepath):
    """Execute sql statements from the file."""
    db = get_db()

    with current_app.open_resource(filepath) as f:
        db.executescript(f.read().decode('utf8'))


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    import_sql('database/schema.sql')
    click.echo('Initialized the database.')


@click.command('import-mock-data')
@with_appcontext
def import_mock_data_command():
    """Insert mock data to database tables."""
    import_sql('database/mock_data.sql')
    click.echo('Inserted mock data to database tables.')


def init_app(app):
    """Initialize app with the database commands."""
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(import_mock_data_command)
