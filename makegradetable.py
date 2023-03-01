import sqlite3


con = sqlite3.connect("gbdb.db")
cur = con.cursor()

data = cur.execute("SELECT id_num, year, section FROM student;")

dictlist = []
for row in data:
    datadict = [row[0],row[1],row[2]]
    dictlist.append(datadict)

con = sqlite3.connect("gbdb.db")
cur = con.cursor()

for obj in dictlist:
    cur.execute("INSERT INTO grade (student_id, class) VALUES (?, ?)", (obj[0], "E30294"))
con.commit()    