"""SQLite locally; MySQL connection settings come only from the environment."""

from contextlib import contextmanager
from importlib.resources import files
import os
import sqlite3


class Database:
    def __init__(self, connection, dialect):
        self.connection = connection
        self.dialect = dialect

    def execute(self, query, params=()):
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                query.replace("?", "%s") if self.dialect == "mysql" else query, params
            )
            if cursor.description:
                names = [column[0] for column in cursor.description]
                return [dict(zip(names, row)) for row in cursor.fetchall()]
            return []
        finally:
            cursor.close()

    def many(self, query, rows):
        if not rows:
            return
        cursor = self.connection.cursor()
        try:
            cursor.executemany(
                query.replace("?", "%s") if self.dialect == "mysql" else query, rows
            )
        finally:
            cursor.close()

    def initialize(self):
        source = (
            files("lse_data").joinpath("sql", f"schema_{self.dialect}.sql").read_text()
        )
        for statement in source.split(";"):
            if statement.strip():
                self.execute(statement)
        self.connection.commit()

    @contextmanager
    def transaction(self):
        try:
            if self.dialect == "mysql":
                self.connection.begin()
            else:
                self.execute("BEGIN")
            yield
            self.connection.commit()
        except BaseException:
            self.connection.rollback()
            raise


@contextmanager
def connect(path=None, mysql=False):
    if mysql:
        import pymysql

        connection = pymysql.connect(
            host=os.getenv("LSE_DB_HOST", "127.0.0.1"),
            port=int(os.getenv("LSE_DB_PORT", "3306")),
            user=os.environ["LSE_DB_USER"],
            password=os.environ["LSE_DB_PASSWORD"],
            database=os.environ["LSE_DB_NAME"],
            charset="utf8mb4",
            autocommit=False,
        )
        db = Database(connection, "mysql")
    else:
        connection = sqlite3.connect(str(path or ":memory:"))
        connection.execute("PRAGMA foreign_keys = ON")
        db = Database(connection, "sqlite")
    try:
        yield db
    finally:
        connection.close()
