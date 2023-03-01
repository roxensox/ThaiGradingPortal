import csv, sqlite3

con = sqlite3.connect("backup.db")
cur = con.cursor()

transfercon = sqlite3.connect("gbdb.db")
transfercursor = transfercon.cursor()

data = cur.execute("SELECT * FROM student;")

for row  in data:
    id_num = row[0]
    section = row[1].split("/")
    year = int(section[0])
    section = int(section[1])
    student_index = row[2]
    gender = row[3]
    thai_name = row[4]

    transfercursor.execute("INSERT INTO student (id_num, year, section, student_index, gender, thai_name) VALUES (?, ?, ?, ?, ?, ?);", (id_num, year, section, student_index, gender, thai_name))

transfercon.commit()