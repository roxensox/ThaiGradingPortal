import sqlite3, helpers, pprint


# This program will allow KKW teachers to access and modify their classes' grades through a web app using Flask as a backend


# This function loads a class from the database and outputs it as a list of dictionaries
def load_class():
    con = sqlite3.connect("gbdb.db")
    cur = con.cursor()

    # Get the specified section from the user [WILL BE REDONE TO TAKE INPUT FROM AN HTML FORM]
    section = tuple([input("Class section: ")])

    # Get the specified class data from the database, and sort it as it is on the class rosters
    out = cur.execute("SELECT * FROM student WHERE class_sec=? ORDER BY gender DESC, id_num", section)

    # Take the column names from the output and put them in a list
    colnames = out.description
    colnamelist = []
    for tup in colnames:
        colnamelist.append(tup[0])

    # Iterate through each row in the SQL output and add it to a list of dictionaries
    outdict = {}
    dictlist = []
    for row in out:
        for i in range(len(colnamelist)):
            outdict[colnamelist[i]] = row[i]
        dictlist.append(outdict)
        outdict = {}

    return dictlist