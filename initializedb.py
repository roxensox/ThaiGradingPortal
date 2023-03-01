import sqlite3
from openpyxl import Workbook, load_workbook
# This program adds all student data to the database
wb = load_workbook(filename = 'roster.xlsx')
i = 1

con = sqlite3.connect('gbdb.db')
cur = con.cursor()

sheet = wb['All']
while sheet[f'A{i}'].value != None:
    id_num = sheet[f'A{i}'].value
    gender = sheet[f'B{i}'].value
    name = sheet[f'C{i}'].value + ' ' + sheet[f'D{i}'].value
    section = sheet[f'E{i}'].value
    section = section.split("/")
    year = section[0]
    section = section[1]
    class_num = sheet[f'F{i}'].value
    cur.execute('INSERT INTO student (id_num, year, section, gender, thai_name, student_index) VALUES (?, ?, ?, ?, ?, ?)', (id_num, year, section, gender, name, class_num))
    i += 1

con.commit()