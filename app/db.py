import psycopg2
from psycopg2.extras import DictCursor

import click
from flask import current_app, g
from flask.cli import with_appcontext


def get_db():
    """Connect to PostgreSQL database and return cursor of connection."""
    if 'db' not in g:
        # `g` object is used to store connection for multiple access to a data
        # during a request
        g.db = psycopg2.connect(
            host=current_app.config["DB_HOST"],
            database=current_app.config['DB_NAME'],
            user=current_app.config['DB_USER'],
            password=current_app.config['DB_PASSWORD'],
            port=current_app.config['DB_PORT'],
        )

    return g.db.cursor(cursor_factory=DictCursor)


def close_db(e=None):
    """Close database connection if it exists."""
    db = g.pop('db', None)

    if db is not None:
        db.close()


def import_sql(filepath):
    """Execute sql statements from the file."""
    db = get_db()

    with current_app.open_resource(filepath) as f:
        db.execute(f.read().decode('utf8'))
        g.db.commit()


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
