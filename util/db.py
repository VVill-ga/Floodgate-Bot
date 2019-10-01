import sqlite3
import os

class DbWrapper:
    class __DbWrapper:
        def __init__(self):
            self.conn = sqlite3.connect("bot.db")
            self.c = self.conn.cursor()

            stmt = """create table if not exists members (
                id text not null,
                username text not null,
                email text,
                token text not null,
                verified integer not null default 0
            );"""

            self.c.execute(stmt)

            stmt = """create table if not exists gitlab (
                id text not null,
                gitlab text not null
            );"""

            self.c.execute(stmt)

        def close(self):
            self.conn.commit()
            self.conn.close()

        def new_member(self, id, username, token):
            stmt = "insert into members (id, username, token) values (?, ?, ?);"
            vars = (id, username, token)

            rows = self.c.execute(stmt, vars).rowcount
            self.conn.commit()
            return rows

        def verify_member(self, id, token):
            stmt = "update members set verified = 1 where id = ? and token = ?;"
            vars = (id, token)

            rows = self.c.execute(stmt, vars).rowcount
            self.conn.commit()
            return rows

        def get_email(self, id):
            stmt = "select email from members where id = ?;"
            vars = (id,)

            try:
                email = self.c.execute(stmt, vars).fetchone()[0]
                self.conn.commit()
                return email 
            except:
                return ""

        def get_token(self, id):
            stmt = "select token from members where id = ?;"
            vars = (id,)

            try:
                token = self.c.execute(stmt, vars).fetchone()[0]
                self.conn.commit()
                return token
            except:
                return ""

        def set_email(self, id, email):
            stmt = "update members set email = ? where id = ?;"
            vars = (email, id)

            rows = self.c.execute(stmt, vars).rowcount
            self.conn.commit()
            return rows

        def prompted(self, id):
            stmt = "update members set prompted = 1 where id = ?;"
            vars = (id,)

            rows = self.c.execute(stmt, vars).rowcount
            self.conn.commit()
            return rows

        def is_user_verified(self, id):
            stmt = "select verified from members where id = ?;"
            vars = (id,)

            try:
                return self.c.execute(stmt, vars).fetchone()[0] == 1
            except:
                return False

        def is_user_gitlab_registered(self, id):
            stmt = "select gitlab from gitlab where id = ?;"
            vars = (id,)

            try:
                return self.c.execute(stmt, vars).fetchone()[0] == 1
            except:
                return False

        def register_user_gitlab(self, id, gitlab):
            stmt = "insert into gitlab (id, gitlab) values (?, ?);"
            vars = (id, gitlab)

            rows = self.c.execute(stmt, vars).rowcount
            self.conn.commit()
            return rows

    # Singleton definitions
    # https://python-3-patterns-idioms-test.readthedocs.io/en/latest/Singleton.html
    instance = None
    def __init__(self):
        if not DbWrapper.instance:
            DbWrapper.instance = DbWrapper.__DbWrapper()
    def __getattr__(self, name):
        return getattr(self.instance, name)
