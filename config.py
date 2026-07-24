"""Configuration values for local development and optional MySQL deployment."""
import os


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")
os.makedirs(INSTANCE_DIR, exist_ok=True)


def _load_env_file():
    """Load simple KEY=VALUE settings from a local .env file when present."""
    env_file = os.path.join(BASE_DIR, ".env")
    if not os.path.exists(env_file):
        return

    with open(env_file, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"\'')
            if key and key not in os.environ:
                os.environ[key] = value


_load_env_file()


def get_database_uri():
    """Use an explicit MySQL URI when available, then MySQL env vars, else fallback to SQLite."""
    database_url = os.environ.get("DATABASE_URL")
    if database_url:
        return database_url

    mysql_user = os.environ.get("MYSQL_USER")
    mysql_password = os.environ.get("MYSQL_PASSWORD", "")
    mysql_host = os.environ.get("MYSQL_HOST", "127.0.0.1")
    mysql_port = os.environ.get("MYSQL_PORT", "3306")
    mysql_db = os.environ.get("MYSQL_DATABASE")

    if mysql_user and mysql_db:
        password_segment = f":{mysql_password}" if mysql_password else ""
        return f"mysql+pymysql://{mysql_user}{password_segment}@{mysql_host}:{mysql_port}/{mysql_db}"

    return "sqlite:///" + os.path.join(INSTANCE_DIR, "online_exam.db")


class Config:
    """Base Flask configuration."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-development-key")
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
