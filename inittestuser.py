# This program adds permissions to access all classes for user 1 for testing
import sqlite3
from app import connect
from helpers import select

con, cur = connect()
data = select("gbdb.db", "SELECT DISTINCT class_sec FROM student;")

for section in data:
    cur.execute("INSERT INTO user_subject (user, subject, class_section) VALUES (1, 30294, ?)", (section['class_sec'],))
    
con.commit()

