import sqlite3
import os

class DbWrapper:
    def __init__(self):
        self.conn = sqlite3.connect("bot.db")
        self.c = self.conn.cursor()

        stmt = """create table if not exists members (
            id text not null,
            token text not null,
            verified integer not null default 0
        );"""

        self.c.execute(stmt)

    def close(self):
        print("closing db")
        self.conn.commit()
        self.conn.close()

    def new_member(self, id, token):
        stmt = "insert into members (id, token) values (?, ?);"
        vars = (id, token)

        rows = self.c.execute(stmt, vars).rowcount
        self.conn.commit()
        return rows

    def verify_member(self, id, token):
        stmt = "update members set verified = 1 where id = ? and token = ?;"
        vars = (id, token)

        rows = self.c.execute(stmt, vars).rowcount
        self.conn.commit()
        return rows

    def get_token(self, id):
        stmt = "select token from members where id = ?;"
        vars = (id,)

        token = self.c.execute(stmt, vars).fetchone()[0]
        self.conn.commit()
        return token