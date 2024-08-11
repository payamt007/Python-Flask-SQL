import base64
import os

import bcrypt
from sqlalchemy import create_engine, text


# Function to hash the password
def hash_password(password):
    # Generate a salt
    salt = bcrypt.gensalt()
    # Hash the password with the generated salt
    hashed_pass = bcrypt.hashpw(password.encode("utf-8"), salt)
    hashed_password_base64 = base64.b64encode(hashed_pass).decode("utf-8")
    return hashed_password_base64


def insert_admin_to_db():
    engine = create_engine(os.environ.get("DATABASE_URL"))
    # engine = create_engine("postgresql+psycopg://postgres:ratestask@127.0.0.1:5433/postgres")
    admin_username = "admin"
    admin_password = "admin-pass"

    with engine.connect() as conn:
        conn.execute(
            text("""
            CREATE TABLE users
            (
                id       bigserial,
                username varchar(50),
                password varchar(1000)
            )""")
        )
        conn.commit()
        conn.execute(
            text("INSERT INTO users(username, password) VALUES (:username, :password)"),
            {"username": admin_username, "password": hash_password(admin_password)},
        )
        conn.commit()


if __name__ == "__main__":
    insert_admin_to_db()
