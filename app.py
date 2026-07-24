import click
from flask import Flask
from config import Config
from extensions import db, login_manager, csrf


def _migrate_user_department_column(app):
    """Add the department column to an existing user table in place.

    Older databases created before the teacher registration feature was added
    will not have this column, causing student registration inserts to fail.
    """
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    if "user" not in inspector.get_table_names():
        return
    existing_columns = {col["name"] for col in inspector.get_columns("user")}
    with db.engine.begin() as connection:
        if "department" not in existing_columns:
            connection.execute(text("ALTER TABLE user ADD COLUMN department VARCHAR(120)"))


def _migrate_result_proctoring_columns(app):
    """Add camera_verified/face_violations columns to an existing SQLite DB in place.

    db.create_all() only creates missing tables, not missing columns on a
    table that already exists, so a database created before the webcam
    proctoring feature was added needs these columns backfilled by hand.
    Safe to run every startup: it checks for the column before adding it.
    """
    from sqlalchemy import inspect, text
    inspector = inspect(db.engine)
    if "result" not in inspector.get_table_names():
        return
    existing_columns = {col["name"] for col in inspector.get_columns("result")}
    with db.engine.begin() as connection:
        if "camera_verified" not in existing_columns:
            connection.execute(text("ALTER TABLE result ADD COLUMN camera_verified BOOLEAN NOT NULL DEFAULT 0"))
        if "face_violations" not in existing_columns:
            connection.execute(text("ALTER TABLE result ADD COLUMN face_violations INTEGER NOT NULL DEFAULT 0"))


def create_app(config_class=Config):
    """Build and return the configured Flask application."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = "main.login"
    login_manager.login_message_category = "warning"
    from routes import main
    app.register_blueprint(main)
    with app.app_context():
        try:
            db.create_all()
            _migrate_user_department_column(app)
            _migrate_result_proctoring_columns(app)
        except Exception as exc:
            app.logger.error("Database initialization failed: %s", exc, exc_info=True)

    @app.cli.command("create-admin")
    @click.option("--name", prompt="Administrator name")
    @click.option("--email", prompt="Administrator email")
    @click.password_option(confirmation_prompt=True)
    def create_admin(name, email, password):
        """Create or promote an administrator without exposing admin registration publicly."""
        from models import User
        account = User.query.filter_by(email=email.lower()).first()
        if account:
            account.name = name
            account.role = "Admin"
            account.set_password(password)
            message = "Existing account promoted to Administrator."
        else:
            account = User(name=name, email=email.lower(), role="Admin")
            account.set_password(password)
            db.session.add(account)
            message = "Administrator account created."
        db.session.commit()
        click.echo(message)
    return app


if __name__ == "__main__":
    create_app().run(debug=True)
