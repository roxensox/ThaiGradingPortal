import sqlite3
from flask import session, redirect
from functools import wraps
# This file will hold functions that help other modules work more smoothly


class student:
    def __init__(self, id_num, section, gender, name):
        self.id = id_num
        self.section = section
        self.gender = gender
        self.name = name

    def set_nickname(self, nickname):
        self.nickname = nickname


def select(database, query:str, query_variable=None):

    # Declare the cursor
    connection = sqlite3.connect(database)
    cur = connection.cursor()

    # Turn single variables into tuples so the sql executes
    if not isinstance(query_variable, tuple) and query_variable != None:
        query_variable = tuple([query_variable])

    # Execute the select query and put all the names in a list, then get all the data as a list
    if query_variable == None:
        cur.execute(query)
    elif len(query_variable) > 1:
        cur.execute(query, query_variable)
    else:
        cur.execute(query, query_variable)
    names = list(map(lambda x: x[0], cur.description))
    db = cur.fetchall()

    # Initialize the output list
    dictlist = []

    # Create a dictionary for each row, then add it to the output list
    for row in range(len(db)):
        currow = db[row]
        currowdict = {}
        for col in range(len(currow)):
            currowdict[names[col]] = currow[col]
        dictlist.append(currowdict)

    return dictlist


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


if __name__ == '__main__':
    print(select('gbdb.db', 'SELECT * FROM student WHERE class_sec="6/1"'))