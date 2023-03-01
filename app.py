import os

import sqlite3
from sqlite3 import Error
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from functools import wraps
from helpers import login_required, select
from time import time
import datetime

#* Configure application
app = Flask(__name__)

#* Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)



#* Configure SQLite to use my database
def connect():
    connection = None
    try:
        connection = sqlite3.connect("gbdb.db")
        cursor = connection.cursor()
        return (connection, cursor)
    except Error as e:
        print(f"The error '{e}' occurred while loading gradebook data")


#_MAIN INTERFACE
# TODO: Make the homepage!
@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

#_VIEW GRADES
#* Made better SQL queries and optimized this function
@app.route("/grades", methods=["POST"])
@login_required
def grades():
    if request.method == "POST":
        #* Get a list of dictionaries containing class subject, short student number, class section, long student number, thai name and all grades data
        
        #* Translate the posted information into the correct format for use going forward
        section = request.form.get("section")[1:-1].split(",")
        for i in range(len(section)):
            section[i] = section[i].strip()
        
        roster = select("gbdb.db", "SELECT class, student_index, year, section, id_num, thai_name, pre_mid, midterm, post_mid, final, (year || '/' || section) AS class_sec FROM student JOIN grade ON student_id = id_num WHERE year = ? AND section = ? AND class = ? ORDER BY student_index;", (section[0], section[1], request.form.get("subject")))
        #* Get a list of dictionaries of all class sections
        classes = select("gbdb.db", "SELECT DISTINCT (grade_level || '/' || class_section) AS class FROM user_subject WHERE user = ? ORDER BY grade_level, class_section;", (session.get("user_id")))
        if len(classes) < 1:
            classes = {"grade_level": 0, "class_section": 0}

        #* Get the list of subjects to put in the dropdown menu on the grade viewing page
        subjects = []
        data = select("gbdb.db", "SELECT DISTINCT subject FROM user_subject WHERE user = ? AND grade_level = ? AND class_section = ?;", (session.get("user_id"), int(section[0]), int(section[1])))
        for row in data:
            subjects.append(row["subject"])
        print(subjects)

        #* Get the current subject specified from the posted form
        curr_subject = request.form.get("subject")
        if curr_subject not in subjects:
            curr_subject = subjects[0]

        #* This part adds two keys to each row of data in roster
        gradeweights = [['pre_mid', 25], ['midterm', 20], ['post_mid', 25], ['final', 30]]
        for row in roster:
            graded = 0
            total = 0
            for segment in gradeweights:
                if row[segment[0]] != None:
                    total += row[segment[0]] / segment[1]
                    graded += 1
            if graded > 0:
                row['percent'] = "{:.0f}%".format(total / graded * 100)
            else:
                row['percent'] = "0%"
        
        #* Pass the roster file, the list of classes, the list of subjects, and the currently selected subject to grades.html
        return render_template("grades.html", roster = roster, classes = classes, subjects = subjects, curr_subject = curr_subject)

#_CHANGE GRADES
@app.route("/editgrades", methods=["GET","POST"])
def changegrades():
    return render_template("changegrades.html")

#_REGISTRATION PAGE
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email")
        username = request.form.get("username")
        password = request.form.get("password")

        if not (email or username or password):
            flash("One or more inputs missing")
            return redirect("/register")

        dbsearch = select("gbdb.db", "SELECT * FROM user WHERE email = ?;", (email))
        if len(dbsearch) > 0:
            flash('An account already exists with this email')
            return redirect("/register")

        dbsearch = select("gbdb.db", "SELECT * FROM user WHERE username = ?;", (username))
        if len(dbsearch) > 0:
            flash('Username taken')
            return redirect("/register")

        con, cur = connect()
        cur.execute("INSERT INTO user (username, hash, email, confirmed) VALUES (?, ?, ?, 'N');", (username, generate_password_hash(password), email))
        con.commit()
        flash('Registered successfully')
        id_num = select("gbdb.db", "SELECT user_id FROM user WHERE username = ?;", username)
        id_num = id_num[0]['user_id']
        session["username"] = username
        session["user_id"] = id_num
        session["permissions"] = []
        return redirect("/")
    else:
        return render_template("register.html")

#_ABOUT PAGE
@app.route("/about", methods=["GET"])
def about():
    return render_template("about.html")

#_CLASS LIST
@app.route("/classes", methods=["GET","POST"])
def classmenu():
    return render_template("classlist.html")

#_CLASS LIST BY SUBJECT
@app.route("/subjectsections", methods=["GET", "POST"])
@login_required
def subjectclassmenu():
    if request.method == "POST":

        #* Get the subject code chosen from the class selection page
        subject_code = request.form.get("subject")

        #* Get all class information from the database where the user has permission to access it and it has the same subject code
        con, cur = connect()
        subject_data = cur.execute("SELECT grade_level, class_section, subject, (grade_level || '/' || class_section) AS class_sec FROM user_subject WHERE user = ? AND subject = ? ORDER BY grade_level, class_section;", (session.get("user_id"), subject_code))
        
        #* Transfer all the data from the sqlite cursor to a list so it can be reused without relocating the cursor, then close the connection to the db
        subject_data_list = []
        for row in subject_data:
            subject_data_list.append(row)
        con.close()
        subject_data = subject_data_list
        
        #* Make a list of each grade level that appears in the data
        levels = []
        for row in subject_data:
            if row[0] not in levels:
                levels.append(row[0])

        return render_template("subjectclasslist.html", subject_data = subject_data, levels = levels, subject=subject_code)
    else:
        return render_template("index.html")

#_LOGIN PAGE
@app.route("/login", methods=["GET","POST"])
def log_in():
    if request.method == "POST":
        #* Get the login information and do the standard database checks
        username = request.form.get("username")
        password = request.form.get("password")
        if not username or not password:
            flash("Must provide a username and password")
            return redirect("/login")
        dbsearch = select("gbdb.db", "SELECT * FROM user WHERE username = ?", username)
        if len(dbsearch) == 0:
            flash(f"{username} is not a registered user")
            return redirect("/login")
        if not check_password_hash(dbsearch[0]["hash"], password):
            flash("Incorrect password")
            return redirect("/login")

        #* This stores the user's user ID
        session["user_id"] = dbsearch[0]["user_id"]
        
        #* This generates the user's permissions using the user_subject table
        data = select("gbdb.db", "SELECT subject, grade_level, class_section FROM user_subject WHERE user = ? ORDER BY subject, grade_level, class_section", (session.get("user_id")))
        permissions = []
        gradelevels = []
        subjects = []
        for row in data:
            #_ALL OF THESE LISTS SHOULD ALREADY BE SORTED BY THE SQL QUERY
            #* Create a permission token (tuple) containing the grade level, class section and subject code for each session the user has access to
            permissions.append((row["grade_level"],row["class_section"],row["subject"]))

            #* Create a list of all grade levels the user has access to (for generating the class selection page)
            if row["grade_level"] not in gradelevels:
                gradelevels.append(row["grade_level"])
            
            #* Create a list of all subjects the user has access to (also for generating the class selection page)
            if row["subject"] not in subjects:
                subjects.append(row["subject"])

    #_SESSION INITIALIZATION ON LOGIN
    # TODO: ADD A FUNCTION TO CHECK IF THE USER'S PERMISSIONS ALL CORRESPOND TO CLASS DATA. IF NOT, BUILD IT IN THE DB
    #* Set the session up and send the user to home with a success message
        #* This stores the generic permissions list containing each class subject/section pair
        session["permissions"] = permissions
        #* This stores the subjects the user has access to
        session["subjects"] = subjects
        #* This stores the information of which grade levels the user has access to
        session["levels"] = gradelevels
        #* This stores the user's username - used for personalized flash messages and profiles
        session["username"] = username
        #* This stores admin status
        if dbsearch[0]['admin'] == "Y":
            session["admin"] = "Y"
        flash(f"Welcome back, {username.capitalize()}.")
        return redirect("/")
    else:
        return render_template("login.html")


#_LOGOUT
@app.route("/logout", methods=["GET"])
def logout():
    session.clear()
    flash("Logged out")
    return redirect("/")

#_ACCOUNT SETTINGS
@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    return render_template("settings.html")

#_CHANGE USERNAME
@app.route("/changeusername", methods=["POST"])
@login_required
def changeusr():
    new_name = request.form.get("newusername")
    data = select("gbdb.db", "SELECT * FROM user WHERE username = ?", (new_name))
    if len(data) > 0:
        flash("Username taken")
        return redirect("/settings")
    con, cur = connect()
    cur.execute("UPDATE user SET username = ? WHERE user_id = ?", (new_name, session.get("user_id")))
    con.commit()
    session["username"] = new_name
    flash(f"Username updated. You are now signed in as {new_name}")
    return redirect("/settings")

#_CHANGE PASSWORD
@app.route("/changepassword", methods=["POST"])
@login_required
def changepw():
    new_password = request.form.get("password")
    old_password = request.form.get("oldpass")
    real_old_password = select("gbdb.db", "SELECT hash FROM user WHERE user_id = ?", (session.get("user_id")))[0]["hash"]
    if check_password_hash(real_old_password, new_password):
        flash("New password cannot be the same as the old password")
        return redirect("/settings")
    if not check_password_hash(real_old_password, old_password):
        flash("Old password is incorrect")
        return redirect("/settings")
    con, cur = connect()
    cur.execute("UPDATE user SET hash = ? WHERE user_id = ?", (generate_password_hash(new_password), session.get("user_id")))
    con.commit()
    flash("Password updated")
    return redirect("/settings")


if __name__ == "__main__":
    app.run(debug=True)