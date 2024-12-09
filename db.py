import sqlite3
from const import DB_NAME

def get_db():
    return sqlite3.connect(DB_NAME)
