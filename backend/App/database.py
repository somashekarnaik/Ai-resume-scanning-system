import os
import shutil
import sqlite3
from pathlib import Path


def _resolve_db_path() -> str:
    env_path = os.getenv("DATABASE_PATH")
    if env_path:
        db_path = Path(env_path)
        try:
            db_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        return str(db_path)

    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        tmp_db = Path("/tmp/resume_scanner.db")
        try:
            tmp_db.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        if not tmp_db.exists():
            for candidate in [
                Path(__file__).resolve().parents[2] / "resume_scanner.db",
                Path(__file__).resolve().parents[1] / "resume_scanner.db",
                Path("resume_scanner.db"),
            ]:
                if candidate.exists():
                    try:
                        shutil.copy(candidate, tmp_db)
                        break
                    except Exception:
                        pass
        return str(tmp_db)

    return "resume_scanner.db"



def get_connection():
    connection = sqlite3.connect(_resolve_db_path())
    connection.row_factory = sqlite3.Row
    return connection


def create_tables():

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY
                AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL

        )
    """)


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resumes (

            id INTEGER PRIMARY KEY
                AUTOINCREMENT,

            user_id INTEGER,

            filename TEXT,

            extracted_text TEXT,

            score REAL

        )
    """)


    connection.commit()

    connection.close()


def create_user(
    name,
    email,
    password
):

    connection = get_connection()

    cursor = connection.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO users
            (name, email, password)
            VALUES (?, ?, ?)
            """,
            (
                name,
                email,
                password
            )
        )

        connection.commit()

        user_id = cursor.lastrowid

        return user_id

    except sqlite3.IntegrityError:

        return None

    finally:

        connection.close()


def get_user(
    email,
    password
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE email = ?
        AND password = ?
        """,
        (
            email,
            password
        )
    )


    user = cursor.fetchone()

    connection.close()

    return user


def save_resume(
    user_id,
    filename,
    text,
    score
):

    connection = get_connection()

    cursor = connection.cursor()


    cursor.execute(
        """
        INSERT INTO resumes
        (
            user_id,
            filename,
            extracted_text,
            score
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            user_id,
            filename,
            text,
            score
        )
    )


    connection.commit()

    connection.close()